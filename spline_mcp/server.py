"""FastMCP server for Spline code generation and asset management."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from spline_mcp import __version__
from spline_mcp.config import get_logger_instance, get_settings, setup_logging
from spline_mcp.tools import (
    register_asset_tools,
    register_generation_tools,
    register_helper_tools,
    register_integration_tools,
)

logger = get_logger_instance("spline-mcp.server")

APP_NAME = "spline-mcp"
APP_VERSION = __version__


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

    # Register tool groups
    register_generation_tools(app)
    register_asset_tools(app)
    register_helper_tools(app)
    register_integration_tools(app)

    # Log registered tools
    logger.info(
        "Tools registered",
        generation=[
            "generate_react_component",
            "generate_vanilla_js",
            "generate_nextjs_component",
            "generate_event_handler",
            "generate_variable_binding",
            "generate_full_integration",
        ],
        assets=[
            "download_scene",
            "validate_scene",
            "list_cached_scenes",
            "clear_cache",
            "get_cache_stats",
        ],
        helpers=[
            "build_export_url",
            "parse_scene_url",
            "list_event_types",
            "get_event_documentation",
            "generate_snippet",
        ],
        integration=[
            "get_websocket_status",
            "subscribe_to_channel",
            "get_n8n_status",
            "generate_n8n_workflow",
            "trigger_n8n_webhook",
            "get_integration_status",
        ],
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
