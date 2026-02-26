"""Asset manager for downloading and caching Spline scenes."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from spline_mcp.config import get_logger_instance, get_settings

logger = get_logger_instance("spline-mcp.assets")


class SceneMetadata(BaseModel):
    """Metadata for a cached scene."""

    scene_id: str = Field(..., description="Unique scene identifier")
    scene_url: str = Field(..., description="Original scene URL")
    local_path: Path = Field(..., description="Local cache path")
    file_size: int = Field(..., description="File size in bytes")
    content_hash: str = Field(..., description="SHA256 hash of content")
    downloaded_at: str = Field(..., description="Download timestamp")
    is_valid: bool = Field(default=True, description="Whether scene passed validation")


class SplineAssetManager:
    """Manage Spline .splinecode asset downloads and caching."""

    # URL pattern for Spline export URLs
    URL_PATTERN = re.compile(
        r"https?://(?:prod\.spline\.design|.+?)"
        r"/([a-zA-Z0-9_-]+)"
        r"/scene\.splinecode"
    )

    def __init__(
        self,
        cache_dir: Path | None = None,
        max_cache_size_mb: int = 500,
    ) -> None:
        """Initialize the asset manager.

        Args:
            cache_dir: Directory for cached files (defaults to settings.cache_dir)
            max_cache_size_mb: Maximum cache size in megabytes
        """
        settings = get_settings()

        self.cache_dir = cache_dir or settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        self._client: httpx.AsyncClient | None = None

        logger.info(
            "Asset manager initialized",
            cache_dir=str(self.cache_dir),
            max_size_mb=max_cache_size_mb,
        )

    async def __aenter__(self) -> "SplineAssetManager":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    @staticmethod
    def extract_scene_id(url: str) -> str:
        """Extract scene ID from a Spline URL.

        Args:
            url: Spline export URL or scene URL

        Returns:
            Scene ID string

        Raises:
            ValueError: If URL doesn't match expected pattern
        """
        match = SplineAssetManager.URL_PATTERN.search(url)
        if match:
            return match.group(1)

        # Try to extract from any URL with an ID-like segment
        parts = url.rstrip("/").split("/")
        for part in reversed(parts):
            if re.match(r"^[a-zA-Z0-9_-]{10,}$", part):
                return part

        raise ValueError(f"Could not extract scene ID from URL: {url}")

    @staticmethod
    def build_export_url(scene_id: str) -> str:
        """Build the export URL for a scene ID.

        Args:
            scene_id: The scene identifier

        Returns:
            Full export URL
        """
        return f"https://prod.spline.design/{scene_id}/scene.splinecode"

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        return self._client

    async def download_scene(
        self,
        scene_url: str,
        force_refresh: bool = False,
    ) -> SceneMetadata:
        """Download and cache a .splinecode file.

        Args:
            scene_url: URL to the scene or scene ID
            force_refresh: Force re-download even if cached

        Returns:
            SceneMetadata with download information

        Raises:
            httpx.HTTPError: If download fails
        """
        # Normalize URL
        if not scene_url.startswith("http"):
            scene_url = self.build_export_url(scene_url)

        scene_id = self.extract_scene_id(scene_url)
        cached_path = self.cache_dir / f"{scene_id}.splinecode"

        # Check cache
        if cached_path.exists() and not force_refresh:
            logger.info(
                "Using cached scene",
                scene_id=scene_id,
                path=str(cached_path),
            )
            return self._create_metadata(
                scene_id=scene_id,
                scene_url=scene_url,
                local_path=cached_path,
            )

        # Download
        logger.info("Downloading scene", scene_id=scene_id, url=scene_url)

        client = self._get_client()
        response = await client.get(scene_url)
        response.raise_for_status()

        content = response.content

        # Save to cache
        cached_path.write_bytes(content)

        logger.info(
            "Scene downloaded and cached",
            scene_id=scene_id,
            size_bytes=len(content),
            path=str(cached_path),
        )

        # Check cache size and cleanup if needed
        await self._cleanup_if_needed()

        return self._create_metadata(
            scene_id=scene_id,
            scene_url=scene_url,
            local_path=cached_path,
        )

    async def validate_scene(
        self,
        scene_path: Path | None = None,
        scene_url: str | None = None,
    ) -> dict[str, Any]:
        """Validate a .splinecode file.

        Args:
            scene_path: Path to local file
            scene_url: URL to download and validate

        Returns:
            Validation result dictionary
        """
        from spline_mcp.assets.validator import validate_scene_file

        if scene_path:
            return validate_scene_file(scene_path).to_dict()

        if scene_url:
            # Download to temp location and validate
            metadata = await self.download_scene(scene_url)
            result = validate_scene_file(metadata.local_path)
            return result.to_dict()

        return {
            "valid": False,
            "error": "Either scene_path or scene_url must be provided",
        }

    def list_cached_scenes(self) -> list[SceneMetadata]:
        """List all cached scenes.

        Returns:
            List of SceneMetadata for cached scenes
        """
        scenes: list[SceneMetadata] = []

        for file_path in self.cache_dir.glob("*.splinecode"):
            try:
                scene_id = file_path.stem
                scenes.append(self._create_metadata(
                    scene_id=scene_id,
                    scene_url=self.build_export_url(scene_id),
                    local_path=file_path,
                ))
            except Exception as e:
                logger.warning(
                    "Failed to read cached scene metadata",
                    path=str(file_path),
                    error=str(e),
                )

        return scenes

    async def clear_cache(
        self,
        scene_id: str | None = None,
    ) -> dict[str, Any]:
        """Clear cached scenes.

        Args:
            scene_id: Specific scene to clear, or None for all

        Returns:
            Result dictionary with cleared count
        """
        cleared = 0

        if scene_id:
            file_path = self.cache_dir / f"{scene_id}.splinecode"
            if file_path.exists():
                file_path.unlink()
                cleared = 1
                logger.info("Cleared cached scene", scene_id=scene_id)
        else:
            for file_path in self.cache_dir.glob("*.splinecode"):
                file_path.unlink()
                cleared += 1

            logger.info("Cleared all cached scenes", count=cleared)

        return {
            "cleared": cleared,
            "scene_id": scene_id,
        }

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_size = 0
        file_count = 0

        for file_path in self.cache_dir.glob("*.splinecode"):
            total_size += file_path.stat().st_size
            file_count += 1

        return {
            "cache_dir": str(self.cache_dir),
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": self.max_cache_size_bytes // (1024 * 1024),
            "utilization_percent": round(
                (total_size / self.max_cache_size_bytes) * 100, 1
            ),
        }

    def get_local_url(self, scene_id: str) -> str:
        """Generate a local URL for self-hosting.

        Args:
            scene_id: The scene identifier

        Returns:
            Local URL path
        """
        return f"/assets/spline/{scene_id}.splinecode"

    def _create_metadata(
        self,
        scene_id: str,
        scene_url: str,
        local_path: Path,
    ) -> SceneMetadata:
        """Create metadata for a cached scene."""
        stat = local_path.stat()
        content = local_path.read_bytes()
        content_hash = hashlib.sha256(content).hexdigest()[:16]

        from datetime import datetime, timezone

        return SceneMetadata(
            scene_id=scene_id,
            scene_url=scene_url,
            local_path=local_path,
            file_size=stat.st_size,
            content_hash=content_hash,
            downloaded_at=datetime.now(timezone.utc).isoformat(),
        )

    async def _cleanup_if_needed(self) -> None:
        """Clean up cache if it exceeds max size."""
        stats = self.get_cache_stats()

        if stats["total_size_bytes"] > self.max_cache_size_bytes:
            # Remove oldest files until under limit
            files = sorted(
                self.cache_dir.glob("*.splinecode"),
                key=lambda p: p.stat().st_mtime,
            )

            current_size = stats["total_size_bytes"]

            for file_path in files:
                if current_size <= self.max_cache_size_bytes * 0.8:  # 80% threshold
                    break

                size = file_path.stat().st_size
                file_path.unlink()
                current_size -= size

                logger.info(
                    "Removed cached scene to free space",
                    file=file_path.stem,
                    size_freed_bytes=size,
                )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


__all__ = ["SplineAssetManager", "SceneMetadata"]
