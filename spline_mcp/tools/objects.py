"""Object management tools for Spline MCP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from spline_mcp.config import get_logger_instance, get_settings

if TYPE_CHECKING:
    pass

logger = get_logger_instance("spline-mcp.tools.objects")


def register_object_tools(app: FastMCP) -> None:
    """Register 3D object management tools."""

    @app.tool()
    async def list_objects(scene_id: str) -> list[dict[str, Any]]:
        """List all objects in a Spline scene.

        Args:
            scene_id: The unique identifier of the scene

        Returns:
            List of object dictionaries
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            objects = await client.list_objects(scene_id)
            logger.info("Listed objects", scene_id=scene_id, count=len(objects))
            return [obj.model_dump() for obj in objects]

    @app.tool()
    async def get_object(scene_id: str, object_id: str) -> dict[str, Any]:
        """Get details of a specific 3D object.

        Args:
            scene_id: The unique identifier of the scene
            object_id: The unique identifier of the object

        Returns:
            Object details including position, rotation, scale
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            obj = await client.get_object(scene_id, object_id)
            logger.info("Retrieved object", scene_id=scene_id, object_id=object_id)
            return obj.model_dump()

    @app.tool()
    async def create_object(
        scene_id: str,
        name: str,
        object_type: str,
        position: list[float] | None = None,
        rotation: list[float] | None = None,
        scale: list[float] | None = None,
    ) -> dict[str, Any]:
        """Create a new 3D object in a scene.

        Args:
            scene_id: The unique identifier of the scene
            name: Name for the new object
            object_type: Type of object (mesh, cube, sphere, light, camera, etc.)
            position: Optional XYZ position [x, y, z]
            rotation: Optional XYZ rotation in degrees [x, y, z]
            scale: Optional XYZ scale [x, y, z]

        Returns:
            Created object details
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            obj = await client.create_object(
                scene_id=scene_id,
                name=name,
                object_type=object_type,
                position=position,
                rotation=rotation,
                scale=scale,
            )
            logger.info(
                "Created object",
                scene_id=scene_id,
                object_id=obj.id,
                name=name,
                type=object_type,
            )
            return obj.model_dump()

    @app.tool()
    async def update_object(
        scene_id: str,
        object_id: str,
        name: str | None = None,
        position: list[float] | None = None,
        rotation: list[float] | None = None,
        scale: list[float] | None = None,
        visible: bool | None = None,
    ) -> dict[str, Any]:
        """Update properties of a 3D object.

        Args:
            scene_id: The unique identifier of the scene
            object_id: The unique identifier of the object
            name: Optional new name
            position: Optional new XYZ position
            rotation: Optional new XYZ rotation in degrees
            scale: Optional new XYZ scale
            visible: Optional visibility toggle

        Returns:
            Updated object details
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        updates: dict[str, Any] = {}
        if name is not None:
            updates["name"] = name
        if position is not None:
            updates["position"] = position
        if rotation is not None:
            updates["rotation"] = rotation
        if scale is not None:
            updates["scale"] = scale
        if visible is not None:
            updates["visible"] = visible

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            obj = await client.update_object(scene_id, object_id, **updates)
            logger.info("Updated object", scene_id=scene_id, object_id=object_id)
            return obj.model_dump()

    @app.tool()
    async def delete_object(scene_id: str, object_id: str) -> dict[str, Any]:
        """Delete an object from a scene.

        Args:
            scene_id: The unique identifier of the scene
            object_id: The unique identifier of the object to delete

        Returns:
            Confirmation of deletion
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            success = await client.delete_object(scene_id, object_id)
            logger.info("Deleted object", scene_id=scene_id, object_id=object_id)
            return {"deleted": success, "object_id": object_id}
