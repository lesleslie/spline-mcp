"""Asset management MCP tools."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from spline_mcp.assets import SplineAssetManager
from spline_mcp.config import get_logger_instance, get_settings

logger = get_logger_instance("spline-mcp.tools.assets")


def register_asset_tools(app: FastMCP) -> None:
    """Register asset management tools."""

    @app.tool()
    async def download_scene(
        scene_url: str,
        force: bool = False,
    ) -> dict[str, Any]:
        """Download and cache a .splinecode file.

        Args:
            scene_url: URL to the scene or scene ID
            force: Force re-download even if cached

        Returns:
            Scene metadata and cache information
        """
        settings = get_settings()

        async with SplineAssetManager(
            cache_dir=settings.cache_dir,
            max_cache_size_mb=settings.max_cache_size_mb,
        ) as manager:
            try:
                metadata = await manager.download_scene(scene_url, force_refresh=force)

                logger.info(
                    "Downloaded scene",
                    scene_id=metadata.scene_id,
                    file_size=metadata.file_size,
                )

                return {
                    "success": True,
                    "scene_id": metadata.scene_id,
                    "scene_url": metadata.scene_url,
                    "local_path": str(metadata.local_path),
                    "file_size": metadata.file_size,
                    "content_hash": metadata.content_hash,
                    "downloaded_at": metadata.downloaded_at,
                    "is_valid": metadata.is_valid,
                    "local_url": manager.get_local_url(metadata.scene_id),
                }

            except Exception as e:
                logger.error(
                    "Failed to download scene",
                    scene_url=scene_url,
                    error=str(e),
                )
                return {
                    "success": False,
                    "error": str(e),
                    "scene_url": scene_url,
                }

    @app.tool()
    async def validate_scene(
        scene_path: str | None = None,
        scene_url: str | None = None,
    ) -> dict[str, Any]:
        """Validate a .splinecode file.

        Args:
            scene_path: Path to local file
            scene_url: URL to download and validate

        Returns:
            Validation result
        """
        from pathlib import Path

        from spline_mcp.assets import validate_scene_file

        if scene_path:
            result = validate_scene_file(Path(scene_path))
            return result.to_dict()

        if scene_url:
            settings = get_settings()
            async with SplineAssetManager(
                cache_dir=settings.cache_dir,
            ) as manager:
                result = await manager.validate_scene(scene_url=scene_url)
                return result

        return {
            "valid": False,
            "error": "Either scene_path or scene_url must be provided",
        }

    @app.tool()
    async def list_cached_scenes() -> dict[str, Any]:
        """List all cached .splinecode files.

        Returns:
            List of cached scenes with metadata
        """
        settings = get_settings()

        async with SplineAssetManager(
            cache_dir=settings.cache_dir,
        ) as manager:
            scenes = manager.list_cached_scenes()

            return {
                "scenes": [
                    {
                        "scene_id": s.scene_id,
                        "scene_url": s.scene_url,
                        "local_path": str(s.local_path),
                        "file_size": s.file_size,
                        "content_hash": s.content_hash,
                        "downloaded_at": s.downloaded_at,
                        "local_url": manager.get_local_url(s.scene_id),
                    }
                    for s in scenes
                ],
                "total": len(scenes),
                "cache_stats": manager.get_cache_stats(),
            }

    @app.tool()
    async def clear_cache(
        scene_id: str | None = None,
    ) -> dict[str, Any]:
        """Clear cached scenes.

        Args:
            scene_id: Specific scene to clear, or None for all

        Returns:
            Result with cleared count
        """
        settings = get_settings()

        async with SplineAssetManager(
            cache_dir=settings.cache_dir,
        ) as manager:
            result = await manager.clear_cache(scene_id)

            logger.info(
                "Cleared cache",
                scene_id=scene_id,
                cleared_count=result["cleared"],
            )

            return result

    @app.tool()
    async def get_cache_stats() -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache size, file count, and utilization
        """
        settings = get_settings()

        async with SplineAssetManager(
            cache_dir=settings.cache_dir,
        ) as manager:
            return manager.get_cache_stats()


__all__ = ["register_asset_tools"]
