"""FastMCP server for Spline 3D scene orchestration."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from spline_mcp import __version__
from spline_mcp.config import get_logger_instance, get_settings, setup_logging
from spline_mcp.tools import (
    register_event_tools,
    register_material_tools,
    register_object_tools,
    register_runtime_tools,
    register_scene_tools,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

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
        api_base_url=settings.api_base_url,
    )

    app = FastMCP(name=APP_NAME, version=APP_VERSION)

    # Register tool groups
    register_scene_tools(app)
    register_object_tools(app)
    register_material_tools(app)
    register_event_tools(app)
    register_runtime_tools(app)

    # Log registered tools
    logger.info(
        "Tools registered",
        scene=["list_scenes", "get_scene", "create_scene", "delete_scene"],
        objects=[
            "list_objects",
            "get_object",
            "create_object",
            "update_object",
            "delete_object",
        ],
        materials=[
            "list_materials",
            "create_material",
            "apply_material",
        ],
        events=[
            "list_events",
            "create_event",
            "trigger_event",
        ],
        runtime=[
            "get_runtime_state",
            "set_variable",
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
