"""Tool registration for Spline MCP server."""

from __future__ import annotations

from spline_mcp.tools.generation import register_generation_tools
from spline_mcp.tools.assets import register_asset_tools
from spline_mcp.tools.helpers import register_helper_tools
from spline_mcp.tools.integration import register_integration_tools

__all__ = [
    "register_generation_tools",
    "register_asset_tools",
    "register_helper_tools",
    "register_integration_tools",
]
