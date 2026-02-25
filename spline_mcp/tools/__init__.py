"""Tool registration for Spline MCP server."""

from __future__ import annotations

from spline_mcp.tools.events import register_event_tools
from spline_mcp.tools.materials import register_material_tools
from spline_mcp.tools.objects import register_object_tools
from spline_mcp.tools.runtime import register_runtime_tools
from spline_mcp.tools.scenes import register_scene_tools

__all__ = [
    "register_scene_tools",
    "register_object_tools",
    "register_material_tools",
    "register_event_tools",
    "register_runtime_tools",
]
