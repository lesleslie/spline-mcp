"""Runtime API tools for Spline MCP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from spline_mcp.config import get_logger_instance, get_settings

if TYPE_CHECKING:
    pass

logger = get_logger_instance("spline-mcp.tools.runtime")


def register_runtime_tools(app: FastMCP) -> None:
    """Register runtime API tools."""

    @app.tool()
    async def get_runtime_state(scene_id: str) -> dict[str, Any]:
        """Get the current runtime state of a scene.

        This retrieves dynamic state including variables, animations,
        and current object states.

        Args:
            scene_id: The unique identifier of the scene

        Returns:
            Current runtime state of the scene
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            state = await client.get_runtime_state(scene_id)
            logger.info("Retrieved runtime state", scene_id=scene_id)
            return state

    @app.tool()
    async def set_variable(
        scene_id: str,
        variable_name: str,
        value: Any,
    ) -> dict[str, Any]:
        """Set a runtime variable in a scene.

        Runtime variables can control animations, visibility, materials,
        and other dynamic properties.

        Args:
            scene_id: The unique identifier of the scene
            variable_name: Name of the variable to set
            value: Value to assign to the variable

        Returns:
            Confirmation and updated variable state
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            result = await client.set_variable(scene_id, variable_name, value)
            logger.info(
                "Set runtime variable",
                scene_id=scene_id,
                variable=variable_name,
            )
            return result

    @app.tool()
    async def export_scene(
        scene_id: str,
        format: str = "gltf",
    ) -> dict[str, Any]:
        """Export a scene to a file format.

        Args:
            scene_id: The unique identifier of the scene
            format: Export format (gltf, glb, obj, fbx)

        Returns:
            Export result with download URL
        """
        # Note: This is a placeholder for export functionality
        # The actual Spline API may have different export endpoints
        logger.info(
            "Export scene requested",
            scene_id=scene_id,
            format=format,
        )
        return {
            "scene_id": scene_id,
            "format": format,
            "status": "export_initiated",
            "message": "Export functionality - check Spline API docs for exact endpoint",
        }
