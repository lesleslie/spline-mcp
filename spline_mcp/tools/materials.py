"""Material management tools for Spline MCP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from spline_mcp.config import get_logger_instance, get_settings

if TYPE_CHECKING:
    pass

logger = get_logger_instance("spline-mcp.tools.materials")


def register_material_tools(app: FastMCP) -> None:
    """Register material management tools."""

    @app.tool()
    async def list_materials(scene_id: str) -> list[dict[str, Any]]:
        """List all materials in a Spline scene.

        Args:
            scene_id: The unique identifier of the scene

        Returns:
            List of material dictionaries
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            materials = await client.list_materials(scene_id)
            logger.info("Listed materials", scene_id=scene_id, count=len(materials))
            return [mat.model_dump() for mat in materials]

    @app.tool()
    async def create_material(
        scene_id: str,
        name: str,
        color: str = "#ffffff",
        metalness: float = 0.0,
        roughness: float = 0.5,
        opacity: float = 1.0,
        emissive: str | None = None,
    ) -> dict[str, Any]:
        """Create a new material in a scene.

        Args:
            scene_id: The unique identifier of the scene
            name: Name for the new material
            color: Base color as hex string (default: white #ffffff)
            metalness: Metalness factor 0.0-1.0 (default: 0.0)
            roughness: Roughness factor 0.0-1.0 (default: 0.5)
            opacity: Opacity 0.0-1.0 (default: 1.0)
            emissive: Optional emissive color as hex string

        Returns:
            Created material details
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            material = await client.create_material(
                scene_id=scene_id,
                name=name,
                color=color,
                metalness=metalness,
                roughness=roughness,
                opacity=opacity,
                emissive=emissive,
            )
            logger.info(
                "Created material",
                scene_id=scene_id,
                material_id=material.id,
                name=name,
            )
            return material.model_dump()

    @app.tool()
    async def apply_material(
        scene_id: str,
        object_id: str,
        material_id: str,
    ) -> dict[str, Any]:
        """Apply a material to a 3D object.

        Args:
            scene_id: The unique identifier of the scene
            object_id: The unique identifier of the target object
            material_id: The unique identifier of the material to apply

        Returns:
            Updated object details
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            obj = await client.apply_material(scene_id, object_id, material_id)
            logger.info(
                "Applied material",
                scene_id=scene_id,
                object_id=object_id,
                material_id=material_id,
            )
            return obj.model_dump()
