"""CLI for Spline MCP server."""

from __future__ import annotations

import asyncio
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from spline_mcp import __version__
from spline_mcp.config import get_settings, setup_logging

app = typer.Typer(help="Spline MCP - Code generation and asset management")
console = Console()


@app.callback()
def callback(ctx: typer.Context) -> None:
    """Handle --config flag to set defaults."""
    settings = get_settings()
    setup_logging(settings)


@app.command()
def serve(
    http: bool = False,
    port: int = 3048,
    host: str = "127.0.0.1",
    verbose: bool = False,
) -> None:
    """Start the MCP server."""
    settings = get_settings()

    if http:
        console.print(f"[yellow]Starting HTTP server on {host}:{port}[/]")
        # Import and run HTTP mode
        import uvicorn

        from spline_mcp.server import get_app

        app_instance = get_app()
        uvicorn.run(app_instance.http_app, host=host, port=port)
    else:
        console.print("[green]Starting stdio MCP server[/]")
        from spline_mcp.server import get_app

        app_instance = get_app()
        # Run in stdio mode
        asyncio.run(app_instance.run_stdio_async())


@app.command()
def health() -> None:
    """Health check for MCP server."""
    console.print("[green]Health check passed[/]")


@app.command()
def generate(
    scene_url: str,
    framework: str = typer.Option("react", "vanilla", "nextjs"),
    output: str = typer.Option(".", help="Output directory"),
    name: str = "SplineScene",
    typescript: bool = True,
    websocket: bool = False,
    websocket_url: str = "ws://localhost:8690",
) -> None:
    """Generate integration code for a Spline scene."""
    from pathlib import Path

    from spline_mcp.generators.base import GenerationOptions
    from spline_mcp.generators.react import ReactGenerator
    from spline_mcp.generators.vanilla import VanillaJSGenerator
    from spline_mcp.generators.nextjs import NextJSGenerator

    settings = get_settings()

    # Normalize URL
    if not scene_url.startswith("http"):
        scene_url = f"https://prod.spline.design/{scene_url}/scene.splinecode"

    # Create options
    options = GenerationOptions(
        component_name=name,
        typescript=typescript,
        lazy_load=settings.lazy_load,
        ssr_placeholder=settings.ssr_placeholder,
        include_websocket=websocket,
        websocket_url=websocket_url,
        indent_spaces=settings.indent_spaces,
        semicolons=settings.semicolons,
    )

    # Select generator
    generators = {
        "react": ReactGenerator,
        "vanilla": VanillaJSGenerator,
        "nextjs": NextJSGenerator,
    }

    generator = generators[framework](options)
    code = generator.generate_component(scene_url, options)

    # Output
    if output != ".":
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if framework == "vanilla":
            ext = "html"
        elif typescript:
            ext = "tsx"
        else:
            ext = "jsx"
        filename = f"{name}.{ext}"
        file_path = output_path / filename

        file_path.write_text(code)
        console.print(f"[green]Generated: {file_path}[/]")
    else:
        # Print to stdout
        console.print(code)

    # Also print install instructions
    console.print(f"\n[blue]Install:[/]")
    console.print(f"  {generator.generate_install_instructions()}")


@app.command()
def download(
    scene_url: str,
    output: str = typer.Option(".", help="Output directory"),
    force: bool = False,
) -> None:
    """Download and cache a .splinecode file."""
    from pathlib import Path
    import asyncio

    from spline_mcp.assets import SplineAssetManager

    settings = get_settings()

    async def _download() -> dict[str, Any]:
        async with SplineAssetManager(
            cache_dir=settings.cache_dir,
            max_cache_size_mb=settings.max_cache_size_mb,
        ) as manager:
            metadata = await manager.download_scene(scene_url, force_refresh=force)
            return metadata

    metadata = asyncio.run(_download())

    if output != ".":
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        scene_id = metadata.scene_id
        dest = output_path / f"{scene_id}.splinecode"

        import shutil

        shutil.copy(str(metadata.local_path), str(dest))
        console.print(f"[green]Downloaded to: {dest}[/]")
    else:
        console.print(f"[green]Cached at: {metadata.local_path}[/]")
        console.print(f"  Scene ID: {metadata.scene_id}")
        console.print(f"  Size: {metadata.file_size:,} bytes")
        console.print(f"  Hash: {metadata.content_hash}")


@app.command()
def cache_stats() -> None:
    """Show cache statistics."""
    from spline_mcp.assets import SplineAssetManager
    import asyncio

    settings = get_settings()

    async def _stats() -> dict[str, Any]:
        async with SplineAssetManager(cache_dir=settings.cache_dir) as manager:
            return manager.get_cache_stats()

    stats = asyncio.run(_stats())

    table = Table(title="Cache Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Cache Directory", stats["cache_dir"])
    table.add_row("File Count", str(stats["file_count"]))
    table.add_row("Total Size", f"{stats['total_size_mb']} MB")
    table.add_row("Max Size", f"{stats['max_size_mb']} MB")
    table.add_row("Utilization", f"{stats['utilization_percent']}%")
    console.print(table)


@app.command()
def list_events() -> None:
    """List all supported Spline event types."""
    from spline_mcp.generators.base import SplineEventType, EVENT_TYPE_DOCS

    table = Table(title="Supported Spline Events")
    table.add_column("Event Type", style="cyan")
    table.add_column("Description", style="white")

    for event in SplineEventType:
        table.add_row(event.value, EVENT_TYPE_DOCS.get(event, "No description"))

    console.print(table)


@app.command()
def integration_status() -> None:
    """Check status of integrations."""
    import asyncio

    from spline_mcp.integrations.websocket import WebSocketClient
    from spline_mcp.integrations.n8n import N8NClient

    settings = get_settings()

    async def _check() -> dict[str, Any]:
        results = {}

        # Check WebSocket
        if settings.websocket_enabled:
            ws_client = WebSocketClient(url=settings.websocket_url)
            connected = await ws_client.connect()
            results["websocket"] = {
                "enabled": True,
                "connected": connected,
                "url": settings.websocket_url,
            }
            await ws_client.disconnect()
        else:
            results["websocket"] = {"enabled": False}

        # Check n8n
        if settings.n8n_enabled:
            n8n_client = N8NClient(base_url=settings.n8n_url)
            available = await n8n_client.check_availability()
            results["n8n"] = {
                "enabled": True,
                "available": available,
                "url": settings.n8n_url,
            }
        else:
            results["n8n"] = {"enabled": False}

        return results

    results = asyncio.run(_check())

    console.print("\n[bold]Integration Status[/bold]\n")

    # WebSocket
    ws = results["websocket"]
    if ws["enabled"]:
        status = "[green]Connected[/]" if ws["connected"] else "[red]Disconnected[/]"
        console.print(f"WebSocket: {status} ({ws['url']})")
    else:
        console.print("WebSocket: [yellow]Disabled[/]")

    # n8n
    n8n = results["n8n"]
    if n8n["enabled"]:
        status = "[green]Available[/]" if n8n["available"] else "[red]Unavailable[/]"
        console.print(f"n8n: {status} ({n8n['url']})")
    else:
        console.print("n8n: [yellow]Disabled[/]")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
