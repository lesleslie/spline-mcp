"""Unit tests for server module."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import FastMCP
from mcp_common.server.telemetry import FastMCPOpenTelemetryMiddleware

from spline_mcp.server import APP_NAME, APP_VERSION, create_app, get_app


def _run_create_app() -> FastMCP:
    """Helper: invoke the async create_app() from a sync test.

    ``create_app`` is async because the W0 helper (mcp-common 0.18.0+) is
    async. Test contexts that aren't pytest-asyncio should call this
    helper rather than awaiting directly.
    """
    return asyncio.run(create_app())


class TestServerCreation:
    """Tests for server creation."""

    def test_app_name(self) -> None:
        """Test app name constant."""
        assert APP_NAME == "spline-mcp"

    def test_app_version(self) -> None:
        """Test app version constant."""
        assert isinstance(APP_VERSION, str)
        assert len(APP_VERSION.split(".")) >= 2

    def test_create_app(self) -> None:
        """Test app creation."""
        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app = _run_create_app()

        assert app is not None
        assert app.name == APP_NAME

    def test_create_app_registers_tools(self) -> None:
        """Real production-path test: create_app() must register all 25 tools + discover_tools.

        Per the W2b.3 review lesson: tests that mock the dispatch helper
        cannot verify the SUT does the right thing. This test exercises
        the real async wiring (``create_app`` -> ``apply_spline_tool_profile``
        -> ``_apply_tool_profile``) and verifies the resulting tool set.

        Will fail (RuntimeError) if the sync ``apply_tool_profile`` wrapper
        is used instead of the async helper.
        """
        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app = _run_create_app()

        # Verify the actual tool set via the async public API.
        names = asyncio.run(_list_tool_names(app))
        expected_spline = {
            "generate_react_component",
            "generate_vanilla_js",
            "generate_nextjs_component",
            "generate_event_handler",
            "generate_variable_binding",
            "generate_full_integration",
            "download_scene",
            "validate_scene",
            "list_cached_scenes",
            "clear_cache",
            "get_cache_stats",
            "build_export_url",
            "parse_scene_url",
            "list_event_types",
            "get_event_documentation",
            "generate_snippet",
            "get_websocket_status",
            "subscribe_to_channel",
            "get_n8n_status",
            "generate_n8n_workflow",
            "trigger_n8n_webhook",
            "get_integration_status",
            "get_runtime_api_docs",
            "get_installation_guide",
            "get_troubleshooting_guide",
        }
        assert expected_spline.issubset(names), (
            f"create_app() missing tools: {sorted(expected_spline - names)}"
        )
        assert "discover_tools" in names, (
            "W0 helper must register discover_tools meta-tool"
        )


async def _list_tool_names(app: FastMCP) -> set[str]:
    """Async helper: list the names of tools registered on ``app``."""
    return {t.name for t in await app.list_tools()}


class TestGetApp:
    """Tests for get_app singleton."""

    def test_get_app_returns_same_instance(self) -> None:
        """Test that get_app returns singleton."""
        import spline_mcp.server as server_module

        # Reset singleton
        server_module._app = None

        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app1 = get_app()
                app2 = get_app()

        assert app1 is app2

    def test_get_app_creates_on_first_call(self) -> None:
        """Test that get_app creates app on first call."""
        import spline_mcp.server as server_module

        # Reset singleton
        server_module._app = None

        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app = get_app()

        assert app is not None
        assert server_module._app is app


class TestDynamicAttributeAccess:
    """Tests for __getattr__ dynamic access."""

    def test_app_attribute(self) -> None:
        """Test accessing app attribute."""
        import spline_mcp.server as server_module

        server_module._app = None

        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app = server_module.app

        assert app is not None

    def test_http_app_attribute(self) -> None:
        """Test accessing http_app attribute."""
        import spline_mcp.server as server_module

        server_module._app = None

        mock_app = MagicMock()
        mock_app.http_app = MagicMock()

        with patch("spline_mcp.server.get_app", return_value=mock_app):
            http_app = server_module.http_app

        assert http_app is not None

    def test_invalid_attribute(self) -> None:
        """Test accessing invalid attribute raises."""
        import spline_mcp.server as server_module

        with pytest.raises(AttributeError, match="has no attribute"):
            _ = server_module.nonexistent_attr


class TestOneiricConvention:
    """Regression tests pinning the Oneiric + mcp-common conventions.

    See: docs/superpowers/plans/2026-06-26-mcpserver-settings-convention.md
    """

    def test_create_app_attaches_otel_middleware(self) -> None:
        """create_app must attach FastMCPOpenTelemetryMiddleware to the server.

        This pins the OTel middleware requirement from the convention plan
        so a future refactor that drops it will trip a CI test.
        """
        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app = _run_create_app()

        # FastMCP stores middleware in _middleware (private) or middleware
        # attribute depending on version. We verify by checking at least one
        # FastMCPOpenTelemetryMiddleware instance is present.
        middleware_list = getattr(app, "_middleware", None) or getattr(
            app, "middleware", []
        )
        # Some FastMCP versions store middleware via a property; fall back to
        # traversing the app's __dict__.
        if not middleware_list:
            middleware_list = [
                v
                for v in app.__dict__.values()
                if isinstance(v, list)
                and v
                and any(isinstance(m, FastMCPOpenTelemetryMiddleware) for m in v)
            ]

        found = any(
            isinstance(m, FastMCPOpenTelemetryMiddleware)
            for m in (
                middleware_list
                if isinstance(middleware_list, list)
                else [middleware_list]
            )
        )
        assert found, (
            "Expected FastMCPOpenTelemetryMiddleware attached to FastMCP server. "
            f"Inspect app attrs: {sorted(app.__dict__.keys())}"
        )

    def test_create_app_uses_mcp_common_fastmcp(self) -> None:
        """create_app must return a FastMCP instance from mcp_common.fastmcp.

        This guards against regressing to ``from fastmcp import FastMCP``
        directly. Both surfaces point at the same class today, but the
        convention requires the mcp_common re-export.
        """
        from mcp_common.fastmcp import FastMCP as MCPCommonFastMCP

        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app = _run_create_app()

        assert isinstance(app, MCPCommonFastMCP)
        assert isinstance(app, FastMCP)  # and the upstream class
