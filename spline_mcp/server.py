"""FastMCP server for Spline code generation and asset management."""

from __future__ import annotations

from typing import Any

from mcp_common.fastmcp import FastMCP
from mcp_common.health import register_http_health_route
from mcp_common.server.telemetry import FastMCPOpenTelemetryMiddleware
from mcp_common.tools.dispatch import apply_tool_profile

from spline_mcp import __version__
from spline_mcp.config import get_logger_instance, get_settings, setup_logging
from spline_mcp.tools.profiles import PROFILE_REGISTRATIONS, register_all_tool_groups

logger = get_logger_instance("spline-mcp.server")

APP_NAME = "spline-mcp"
APP_VERSION = __version__


def _attach_otel_middleware(app: FastMCP) -> None:
    """Attach the mcp_common OpenTelemetry middleware to the FastMCP app.

    See: docs/superpowers/plans/2026-06-26-mcpserver-settings-convention.md
    """
    middleware = FastMCPOpenTelemetryMiddleware(service_name=APP_NAME)
    app.add_middleware(middleware)


def create_app() -> FastMCP:
    """Create and configure the FastMCP application."""
    settings = get_settings()
    setup_logging(settings)

    logger.info(
        "Initializing spline-mcp server",
        version=APP_VERSION,
        default_framework=settings.default_framework,
        websocket_enabled=settings.websocket_enabled,
        n8n_enabled=settings.n8n_enabled,
    )

    app = FastMCP(name=APP_NAME, version=APP_VERSION)

    # HTTP health endpoint for Claude Code compatibility
    register_http_health_route(
        app,
        service_name=APP_NAME,
        version=APP_VERSION,
    )

    # OpenTelemetry middleware (Bodai convention)
    _attach_otel_middleware(app)

    # Apply tool profile dispatch (SPLINE_TOOL_PROFILE env var).
    #
    # Replaces the previous direct register_*_tools(app) calls. The W0
    # helper from mcp-common 0.18.0+ dispatches by group name and always
    # registers the `discover_tools` meta-tool. The default (no env var)
    # remains FULL = all 25 tools — the previous behavior is preserved.
    #
    # The sync ``apply_tool_profile`` wrapper from mcp-common handles the
    # no-running-loop case via ``asyncio.run``; it raises ``RuntimeError``
    # when called from within a running event loop (forcing async callers to
    # use ``_apply_tool_profile`` instead). At module import time of this
    # create_app() no event loop is running, so this works in normal CLI /
    # HTTP-server startup paths.
    from spline_mcp.tools.profiles import _build_registration_map

    apply_tool_profile(
        app,
        profile_env_var="SPLINE_TOOL_PROFILE",
        registrations=PROFILE_REGISTRATIONS,
        registration_map=_build_registration_map(),
        register_all_fn=register_all_tool_groups,
    )

    return app


_app: FastMCP | None = None


def get_app() -> FastMCP:
    """Get the singleton FastMCP application."""
    global _app
    if _app is None:
        _app = create_app()
    return _app


def __getattr__(name: str) -> Any:
    """Dynamic attribute access for app and http_app."""
    if name == "app":
        return get_app()
    if name == "http_app":
        return get_app().http_app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["create_app", "get_app", "APP_NAME", "APP_VERSION"]
