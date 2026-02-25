"""CLI for Spline MCP server."""

from __future__ import annotations

import typer
from rich.console import Console

from spline_mcp import __version__

app = typer.Typer(
    name="spline-mcp",
    help="MCP server for Spline.design 3D scene orchestration",
)
console = Console()


@app.command()
def serve(
    http: bool = typer.Option(
        False,
        "--http",
        help="Enable HTTP transport instead of stdio",
    ),
    port: int = typer.Option(
        3048,
        "--port",
        "-p",
        help="HTTP server port (default: 3048)",
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="HTTP server host",
    ),
) -> None:
    """Start the Spline MCP server."""
    from spline_mcp.server import get_app

    mcp_app = get_app()

    if http:
        console.print(f"[green]Starting Spline MCP HTTP server on {host}:{port}[/green]")
        import uvicorn

        uvicorn.run(mcp_app.http_app, host=host, port=port)
    else:
        console.print("[green]Starting Spline MCP stdio server[/green]")
        mcp_app.run()


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"[bold blue]spline-mcp[/bold blue] version [green]{__version__}[/green]")


@app.command()
def health() -> None:
    """Check server health status."""
    from spline_mcp.client import SplineClient
    from spline_mcp.config import get_settings

    settings = get_settings()

    if not settings.api_key:
        console.print("[red]Error: SPLINE_API_KEY not configured[/red]")
        raise typer.Exit(1)

    console.print("[yellow]Checking Spline API connection...[/yellow]")

    # Quick health check
    try:
        client = SplineClient(settings.api_key, settings.api_base_url)
        console.print("[green]✓ Spline client initialized[/green]")
        console.print(f"  API Base: {settings.api_base_url}")
    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
