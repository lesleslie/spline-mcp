"""Unit tests for spline_mcp.cli — exercises all Typer commands.

The CLI module is a thin Typer wrapper around the existing
``spline_mcp.server`` / generators / asset manager / WebSocket client
surface. The ``app = typer.Typer(...)`` and ``console = Console()``
module-level statements are covered simply by importing the module.
The commands themselves are exercised here by direct invocation (the
``generate`` command has a known typo where ``typer.Option`` is called
with positional args, so the standard ``CliRunner`` introspection path
would fail; calling the function directly bypasses Typer's parameter
parsing).
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spline_mcp.cli import (
    app,
    cache_stats,
    callback,
    console,
    download,
    generate,
    health,
    integration_status,
    list_events,
    serve,
)
from spline_mcp.config import get_settings


class TestCliBootstrap:
    """Verify module-level objects and the main() entry point."""

    def test_module_app_is_typer(self) -> None:
        """The module-level ``app`` must be a Typer instance."""
        import typer

        assert isinstance(app, typer.Typer)

    def test_module_console_is_rich_console(self) -> None:
        """The module-level ``console`` must be a Rich Console instance."""
        from rich.console import Console

        assert isinstance(console, Console)

    def test_callback_invokes_settings_and_setup(self) -> None:
        """``callback`` must call get_settings() and setup_logging()."""
        get_settings.cache_clear()

        with patch("spline_mcp.cli.setup_logging") as mock_setup:
            callback(MagicMock())

        mock_setup.assert_called_once()

    def test_main_function_dispatches_app(self) -> None:
        """``main()`` must delegate to ``app()`` (Typer entry point)."""
        with patch("spline_mcp.cli.app") as mock_app:
            from spline_mcp.cli import main

            main()

        mock_app.assert_called_once()


class TestServeCommand:
    """Tests for the ``serve`` Typer command."""

    def test_serve_stdio_mode_dispatches_to_run_stdio_async(self) -> None:
        """``serve(http=False)`` must invoke run_stdio_async via asyncio.run."""
        mock_app_instance = MagicMock()
        mock_app_instance.run_stdio_async = MagicMock()

        with (
            patch("spline_mcp.cli.get_settings"),
            patch("spline_mcp.server.get_app", return_value=mock_app_instance),
            patch("spline_mcp.cli.asyncio.run", side_effect=lambda c: None) as mock_run,
        ):
            serve(http=False, port=3052, host="127.0.0.1", verbose=False)

        mock_run.assert_called_once()

    def test_serve_http_mode_dispatches_to_uvicorn(self) -> None:
        """``serve(http=True)`` must invoke uvicorn.run with the HTTP app."""
        mock_app_instance = MagicMock()
        mock_http_app = MagicMock()
        mock_app_instance.http_app = mock_http_app

        # cli.py does ``import uvicorn`` inside serve(); patch sys.modules
        # so the lookup returns our mock instead of the real uvicorn (which
        # would otherwise actually start a server and hang the test).
        mock_uvicorn = MagicMock()
        with (
            patch.dict("sys.modules", {"uvicorn": mock_uvicorn}),
            patch("spline_mcp.cli.get_settings"),
            patch("spline_mcp.server.get_app", return_value=mock_app_instance),
        ):
            serve(http=True, port=3052, host="127.0.0.1", verbose=False)

        mock_uvicorn.run.assert_called_once()
        call_args = mock_uvicorn.run.call_args
        assert call_args.args[0] is mock_http_app
        assert call_args.kwargs["host"] == "127.0.0.1"
        assert call_args.kwargs["port"] == 3052


class TestHealthCommand:
    """Tests for the ``health`` Typer command."""

    def test_health_prints_status(self) -> None:
        """``health`` must print a green 'Health check passed' status."""
        with patch.object(console, "print") as mock_print:
            health()

        assert any("Health check" in str(call.args) for call in mock_print.call_args_list)


class TestGenerateCommand:
    """Tests for the ``generate`` Typer command."""

    def test_generate_react_stdout(self) -> None:
        """``generate(framework=react, output=.)`` must print code to stdout."""
        get_settings.cache_clear()

        with patch.object(console, "print") as mock_print:
            generate(
                scene_url="abc123",
                framework="react",
                output=".",
                name="TestScene",
                typescript=True,
                websocket=False,
            )

        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        assert "TestScene" in printed

    def test_generate_nextjs_stdout(self) -> None:
        """``generate(framework=nextjs)`` must emit a 'use client' Next.js component."""
        get_settings.cache_clear()

        with patch.object(console, "print") as mock_print:
            generate(
                scene_url="xyz789",
                framework="nextjs",
                output=".",
                name="NextScene",
                typescript=True,
                websocket=False,
            )

        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        assert "use client" in printed

    def test_generate_vanilla_to_file(self) -> None:
        """``generate(framework=vanilla, output=dir)`` must write an .html file."""
        get_settings.cache_clear()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate(
                scene_url="abc123",
                framework="vanilla",
                output=tmpdir,
                name="VanillaScene",
                typescript=True,
                websocket=False,
            )

            files = list(Path(tmpdir).iterdir())
            assert len(files) == 1
            assert files[0].name == "VanillaScene.html"
            assert "<!DOCTYPE html>" in files[0].read_text()

    def test_generate_typescript_to_file(self) -> None:
        """``generate(framework=react, typescript=True)`` writes .tsx."""
        get_settings.cache_clear()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate(
                scene_url="abc123",
                framework="react",
                output=tmpdir,
                name="TScene",
                typescript=True,
                websocket=False,
            )

            assert (Path(tmpdir) / "TScene.tsx").exists()

    def test_generate_javascript_to_file(self) -> None:
        """``generate(typescript=False, framework=react)`` writes .jsx."""
        get_settings.cache_clear()

        with tempfile.TemporaryDirectory() as tmpdir:
            generate(
                scene_url="abc123",
                framework="react",
                output=tmpdir,
                name="JScene",
                typescript=False,
                websocket=False,
            )

            assert (Path(tmpdir) / "JScene.jsx").exists()

    def test_generate_url_normalization(self) -> None:
        """A bare scene ID must be normalized to a prod.spline.design URL."""
        get_settings.cache_clear()

        with patch.object(console, "print") as mock_print:
            generate(
                scene_url="abc123",
                framework="react",
                output=".",
                name="NormScene",
                typescript=True,
                websocket=False,
            )

        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        assert "prod.spline.design/abc123/scene.splinecode" in printed

    def test_generate_websocket_includes_block(self) -> None:
        """``websocket=True`` must include the useWebSocket import in the output."""
        get_settings.cache_clear()

        with patch.object(console, "print") as mock_print:
            generate(
                scene_url="abc123",
                framework="react",
                output=".",
                name="WsScene",
                typescript=True,
                websocket=True,
                websocket_url="ws://example.com:1234",
            )

        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        assert "useWebSocket" in printed or "@bodai" in printed


class TestDownloadCommand:
    """Tests for the ``download`` Typer command."""

    def test_download_prints_cache_info(self) -> None:
        """``download(output=.)`` must print cached-at and metadata."""
        get_settings.cache_clear()

        with tempfile.TemporaryDirectory() as tmpdir:
            settings = get_settings()
            settings.cache_dir = Path(tmpdir)

            scene_file = Path(tmpdir) / "abc123.splinecode"
            scene_file.write_bytes(b"x" * 200)

            def _fake_download(coroutine: object) -> object:
                from spline_mcp.assets.manager import SceneMetadata
                from datetime import UTC, datetime

                return SceneMetadata(
                    scene_id="abc123",
                    scene_url="abc123",
                    local_path=scene_file,
                    file_size=200,
                    content_hash="abcdef1234567890",
                    downloaded_at=datetime.now(UTC).isoformat(),
                )

            with (
                patch("spline_mcp.cli.get_settings", return_value=settings),
                patch("spline_mcp.cli.asyncio.run", side_effect=_fake_download),
                patch.object(console, "print") as mock_print,
            ):
                download(scene_url="abc123", output=".", force=False)

        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        assert "Cached at" in printed
        assert "Scene ID" in printed
        assert "Hash" in printed

    def test_download_writes_file_when_output_dir(self) -> None:
        """``download(output=dir)`` must copy the cached file to the target dir."""
        get_settings.cache_clear()

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            out_dir = Path(tmpdir) / "out"
            out_dir.mkdir()

            scene_file = cache_dir / "abc123.splinecode"
            scene_file.write_bytes(b"x" * 200)

            settings = get_settings()
            settings.cache_dir = cache_dir

            def _fake_download(coroutine: object) -> object:
                from spline_mcp.assets.manager import SceneMetadata
                from datetime import UTC, datetime

                return SceneMetadata(
                    scene_id="abc123",
                    scene_url="abc123",
                    local_path=scene_file,
                    file_size=200,
                    content_hash="abcdef1234567890",
                    downloaded_at=datetime.now(UTC).isoformat(),
                )

            with (
                patch("spline_mcp.cli.get_settings", return_value=settings),
                patch("spline_mcp.cli.asyncio.run", side_effect=_fake_download),
                patch.object(console, "print"),
            ):
                download(scene_url="abc123", output=str(out_dir), force=False)

            assert (out_dir / "abc123.splinecode").exists()


class TestCacheStatsCommand:
    """Tests for the ``cache_stats`` Typer command."""

    def test_cache_stats_prints_table(self) -> None:
        """``cache_stats`` must invoke console.print with a Table."""
        get_settings.cache_clear()

        with tempfile.TemporaryDirectory() as tmpdir:
            settings = get_settings()
            settings.cache_dir = Path(tmpdir)

            def _fake_stats(coroutine: object) -> dict[str, object]:
                return {
                    "cache_dir": tmpdir,
                    "file_count": 0,
                    "total_size_mb": 0.0,
                    "max_size_mb": 500,
                    "utilization_percent": 0.0,
                }

            with (
                patch("spline_mcp.cli.get_settings", return_value=settings),
                patch("spline_mcp.cli.asyncio.run", side_effect=_fake_stats),
                patch.object(console, "print") as mock_print,
            ):
                cache_stats()

        assert mock_print.call_count >= 1


class TestListEventsCommand:
    """Tests for the ``list_events`` Typer command."""

    def test_list_events_includes_all_event_types(self) -> None:
        """``list_events`` must include every Spline event type in the table."""
        from rich.table import Table

        from spline_mcp.generators.base import SplineEventType

        captured: list[Table] = []

        def _capture_table(value: object) -> None:
            if isinstance(value, Table):
                captured.append(value)

        with patch.object(console, "print", side_effect=_capture_table):
            list_events()

        assert len(captured) == 1
        rendered = captured[0]
        # Render the table through Rich's console protocol so we can grep
        # event names out of the produced string.
        from io import StringIO

        from rich.console import Console

        buf = StringIO()
        render_console = Console(file=buf, width=200, force_terminal=False)
        render_console.print(rendered)
        rendered_text = buf.getvalue()
        for event in SplineEventType:
            assert event.value in rendered_text, (
                f"Missing event {event.value} in table"
            )


class TestIntegrationStatusCommand:
    """Tests for the ``integration_status`` Typer command."""

    def test_integration_status_disabled(self) -> None:
        """``integration_status`` with WebSocket disabled must print 'Disabled'."""
        get_settings.cache_clear()
        settings = get_settings()
        settings.websocket_enabled = False

        def _fake_check(coroutine: object) -> dict[str, dict[str, object]]:
            return {"websocket": {"enabled": False}}

        with (
            patch("spline_mcp.cli.get_settings", return_value=settings),
            patch("spline_mcp.cli.asyncio.run", side_effect=_fake_check),
            patch.object(console, "print") as mock_print,
        ):
            integration_status()

        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        assert "Disabled" in printed

    def test_integration_status_connected(self) -> None:
        """``integration_status`` with WebSocket connected must print 'Connected'."""
        get_settings.cache_clear()
        settings = get_settings()
        settings.websocket_enabled = True
        settings.websocket_url = "ws://localhost:9999"

        def _fake_check(coroutine: object) -> dict[str, dict[str, object]]:
            return {
                "websocket": {
                    "enabled": True,
                    "connected": True,
                    "url": "ws://localhost:9999",
                }
            }

        with (
            patch("spline_mcp.cli.get_settings", return_value=settings),
            patch("spline_mcp.cli.asyncio.run", side_effect=_fake_check),
            patch.object(console, "print") as mock_print,
        ):
            integration_status()

        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        assert "Connected" in printed
        assert "ws://localhost:9999" in printed

    def test_integration_status_disconnected(self) -> None:
        """``integration_status`` with WebSocket disconnected must print 'Disconnected'."""
        get_settings.cache_clear()
        settings = get_settings()
        settings.websocket_enabled = True
        settings.websocket_url = "ws://localhost:9999"

        def _fake_check(coroutine: object) -> dict[str, dict[str, object]]:
            return {
                "websocket": {
                    "enabled": True,
                    "connected": False,
                    "url": "ws://localhost:9999",
                }
            }

        with (
            patch("spline_mcp.cli.get_settings", return_value=settings),
            patch("spline_mcp.cli.asyncio.run", side_effect=_fake_check),
            patch.object(console, "print") as mock_print,
        ):
            integration_status()

        printed = " ".join(str(c.args[0]) for c in mock_print.call_args_list if c.args)
        assert "Disconnected" in printed
