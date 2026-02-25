"""Scene management tools for Spline MCP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from spline_mcp.config import get_logger_instance, get_settings

if TYPE_CHECKING:
    pass

logger = get_logger_instance("spline-mcp.tools.scenes")


def register_scene_tools(app: FastMCP) -> None:
    """Register scene management tools."""

    @app.tool()
    async def list_scenes() -> list[dict[str, Any]]:
        """List all accessible Spline scenes.

        Returns:
            List of scene metadata dictionaries
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            scenes = await client.list_scenes()
            logger.info("Listed scenes", count=len(scenes))
            return scenes

    @app.tool()
    async def get_scene(scene_id: str) -> dict[str, Any]:
        """Get detailed information about a specific scene.

        Args:
            scene_id: The unique identifier of the scene

        Returns:
            Scene details including objects, materials, and events
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            scene = await client.get_scene(scene_id)
            logger.info("Retrieved scene", scene_id=scene_id, name=scene.name)
            return scene.model_dump()

    @app.tool()
    async def create_scene(
        name: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new Spline scene.

        Args:
            name: Name for the new scene
            description: Optional scene description

        Returns:
            Created scene details
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            properties: dict[str, Any] = {}
            if description:
                properties["description"] = description

            scene = await client.create_scene(name, **properties)
            logger.info("Created scene", scene_id=scene.id, name=scene.name)
            return scene.model_dump()

    @app.tool()
    async def delete_scene(scene_id: str) -> dict[str, Any]:
        """Delete a Spline scene.

        Args:
            scene_id: The unique identifier of the scene to delete

        Returns:
            Confirmation of deletion
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            success = await client.delete_scene(scene_id)
            logger.info("Deleted scene", scene_id=scene_id, success=success)
            return {"deleted": success, "scene_id": scene_id}
