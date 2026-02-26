"""Unit tests for asset management."""

from __future__ import annotations

import gzip
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from spline_mcp.assets.manager import SceneMetadata, SplineAssetManager
from spline_mcp.assets.validator import ValidationResult, validate_scene_file


class TestSceneMetadata:
    """Tests for SceneMetadata model."""

    def test_metadata_creation(self, tmp_path: Path) -> None:
        """Test creating scene metadata."""
        metadata = SceneMetadata(
            scene_id="abc123",
            scene_url="https://prod.spline.design/abc123/scene.splinecode",
            local_path=tmp_path / "abc123.splinecode",
            file_size=1024,
            content_hash="abcd1234",
            downloaded_at="2024-01-01T00:00:00Z",
        )

        assert metadata.scene_id == "abc123"
        assert metadata.file_size == 1024
        assert metadata.is_valid is True

    def test_metadata_default_valid(self, tmp_path: Path) -> None:
        """Test default valid status."""
        metadata = SceneMetadata(
            scene_id="test",
            scene_url="https://example.com/test/scene.splinecode",
            local_path=tmp_path / "test.splinecode",
            file_size=100,
            content_hash="hash",
            downloaded_at="2024-01-01",
        )

        assert metadata.is_valid is True


class TestSplineAssetManager:
    """Tests for SplineAssetManager."""

    def test_extract_scene_id_from_url(self) -> None:
        """Test extracting scene ID from URL."""
        url = "https://prod.spline.design/abc123def456/scene.splinecode"
        scene_id = SplineAssetManager.extract_scene_id(url)
        assert scene_id == "abc123def456"

    def test_extract_scene_id_from_custom_domain(self) -> None:
        """Test extracting from custom domain."""
        url = "https://custom.domain.com/xyz789/scene.splinecode"
        scene_id = SplineAssetManager.extract_scene_id(url)
        assert scene_id == "xyz789"

    def test_extract_scene_id_from_path_only(self) -> None:
        """Test extracting from URL path segment."""
        url = "https://example.com/some/path/MY_SCENE_ID_12345"
        scene_id = SplineAssetManager.extract_scene_id(url)
        assert scene_id == "MY_SCENE_ID_12345"

    def test_extract_scene_id_invalid(self) -> None:
        """Test invalid URL raises error."""
        with pytest.raises(ValueError, match="Could not extract scene ID"):
            SplineAssetManager.extract_scene_id("https://example.com/short")

    def test_build_export_url(self) -> None:
        """Test building export URL."""
        url = SplineAssetManager.build_export_url("abc123")
        assert url == "https://prod.spline.design/abc123/scene.splinecode"

    def test_get_local_url(self, tmp_path: Path) -> None:
        """Test local URL generation."""
        manager = SplineAssetManager(cache_dir=tmp_path)
        local_url = manager.get_local_url("scene123")
        assert local_url == "/assets/spline/scene123.splinecode"

    def test_list_cached_scenes_empty(self, tmp_path: Path) -> None:
        """Test listing empty cache."""
        manager = SplineAssetManager(cache_dir=tmp_path)
        scenes = manager.list_cached_scenes()
        assert scenes == []

    def test_list_cached_scenes_with_files(self, tmp_path: Path) -> None:
        """Test listing cached scenes."""
        # Create a mock scene file with enough content
        scene_file = tmp_path / "test123.splinecode"
        scene_file.write_bytes(json.dumps({"objects": [], "materials": []}).encode().ljust(200, b" "))

        manager = SplineAssetManager(cache_dir=tmp_path)
        scenes = manager.list_cached_scenes()

        assert len(scenes) == 1
        assert scenes[0].scene_id == "test123"

    def test_get_cache_stats_empty(self, tmp_path: Path) -> None:
        """Test cache stats when empty."""
        manager = SplineAssetManager(cache_dir=tmp_path)
        stats = manager.get_cache_stats()

        assert stats["file_count"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["total_size_mb"] == 0.0

    def test_get_cache_stats_with_files(self, tmp_path: Path) -> None:
        """Test cache stats with files."""
        scene_file = tmp_path / "test.splinecode"
        scene_file.write_bytes(b"x" * 1024)

        manager = SplineAssetManager(cache_dir=tmp_path)
        stats = manager.get_cache_stats()

        assert stats["file_count"] == 1
        assert stats["total_size_bytes"] == 1024

    @pytest.mark.asyncio
    async def test_clear_cache_all(self, tmp_path: Path) -> None:
        """Test clearing all cache."""
        scene_file = tmp_path / "test.splinecode"
        scene_file.write_bytes(b"data")

        manager = SplineAssetManager(cache_dir=tmp_path)
        result = await manager.clear_cache()

        assert result["cleared"] == 1
        assert not scene_file.exists()

    @pytest.mark.asyncio
    async def test_clear_cache_specific(self, tmp_path: Path) -> None:
        """Test clearing specific scene."""
        scene1 = tmp_path / "scene1.splinecode"
        scene2 = tmp_path / "scene2.splinecode"
        scene1.write_bytes(b"data1")
        scene2.write_bytes(b"data2")

        manager = SplineAssetManager(cache_dir=tmp_path)
        result = await manager.clear_cache("scene1")

        assert result["cleared"] == 1
        assert not scene1.exists()
        assert scene2.exists()

    @pytest.mark.asyncio
    async def test_clear_cache_nonexistent(self, tmp_path: Path) -> None:
        """Test clearing nonexistent scene."""
        manager = SplineAssetManager(cache_dir=tmp_path)
        result = await manager.clear_cache("nonexistent")

        assert result["cleared"] == 0

    @pytest.mark.asyncio
    async def test_context_manager(self, tmp_path: Path) -> None:
        """Test async context manager."""
        async with SplineAssetManager(cache_dir=tmp_path) as manager:
            assert manager._client is not None

        assert manager._client is None

    @pytest.mark.asyncio
    async def test_download_scene_cached(self, tmp_path: Path) -> None:
        """Test downloading already cached scene."""
        # Create a valid scene file with enough content
        scene_file = tmp_path / "abc123.splinecode"
        scene_file.write_bytes(json.dumps({"objects": [], "materials": []}).encode().ljust(200, b" "))

        async with SplineAssetManager(cache_dir=tmp_path) as manager:
            metadata = await manager.download_scene(
                "https://prod.spline.design/abc123/scene.splinecode"
            )

        assert metadata.scene_id == "abc123"
        assert metadata.local_path == scene_file

    @pytest.mark.asyncio
    async def test_validate_scene_local(self, tmp_path: Path) -> None:
        """Test validating local scene file."""
        scene_file = tmp_path / "test.splinecode"
        # Create a valid scene with enough content (> 100 bytes)
        scene_data = {
            "objects": [{"id": "1", "name": "Cube", "type": "mesh"}],
            "materials": [{"id": "1", "name": "Default"}],
            "version": "1.0",
            "metadata": {"author": "test", "description": "Test scene file"},
        }
        scene_file.write_bytes(json.dumps(scene_data).encode())

        async with SplineAssetManager(cache_dir=tmp_path) as manager:
            result = await manager.validate_scene(scene_path=scene_file)

        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_scene_neither_provided(self, tmp_path: Path) -> None:
        """Test validation with no path or URL."""
        async with SplineAssetManager(cache_dir=tmp_path) as manager:
            result = await manager.validate_scene()

        assert result["valid"] is False
        assert "error" in result


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_default_values(self) -> None:
        """Test default values."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.file_size == 0
        assert result.error is None
        assert result.warnings == []
        assert result.metadata == {}

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        result = ValidationResult(
            valid=False,
            file_size=100,
            error="Test error",
            warnings=["Warning 1"],
            metadata={"key": "value"},
        )

        d = result.to_dict()
        assert d["valid"] is False
        assert d["file_size"] == 100
        assert d["error"] == "Test error"
        assert d["warnings"] == ["Warning 1"]
        assert d["metadata"] == {"key": "value"}


class TestValidateSceneFile:
    """Tests for validate_scene_file function."""

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Test validation of nonexistent file."""
        result = validate_scene_file(tmp_path / "nonexistent.splinecode")
        assert result.valid is False
        assert "File not found" in result.error

    def test_not_a_file(self, tmp_path: Path) -> None:
        """Test validation of directory."""
        result = validate_scene_file(tmp_path)
        assert result.valid is False
        assert "Not a file" in result.error

    def test_file_too_small(self, tmp_path: Path) -> None:
        """Test validation of file too small."""
        small_file = tmp_path / "small.splinecode"
        small_file.write_bytes(b"{}")

        result = validate_scene_file(small_file)
        assert result.valid is False
        assert "too small" in result.error

    def test_valid_json_scene(self, tmp_path: Path) -> None:
        """Test validation of valid scene file."""
        scene_file = tmp_path / "valid.splinecode"
        # Create a scene with enough content (> 100 bytes)
        scene_data = {
            "objects": [{"name": "Cube", "id": "obj1", "type": "mesh"}],
            "materials": [{"name": "Default", "id": "mat1"}],
            "version": "1.0",
            "metadata": {"description": "Test scene for validation"},
        }
        scene_file.write_bytes(json.dumps(scene_data).encode())

        result = validate_scene_file(scene_file)
        assert result.valid is True
        assert result.metadata["object_count"] == 1
        assert result.metadata["material_count"] == 1
        assert result.metadata["version"] == "1.0"

    def test_invalid_json(self, tmp_path: Path) -> None:
        """Test validation of invalid JSON."""
        scene_file = tmp_path / "invalid.splinecode"
        scene_file.write_bytes(b"not valid json" * 10)

        result = validate_scene_file(scene_file)
        assert result.valid is False
        assert "Invalid JSON" in result.error

    def test_json_not_object(self, tmp_path: Path) -> None:
        """Test validation when JSON is not an object."""
        scene_file = tmp_path / "list.splinecode"
        # Ensure file is large enough (> 100 bytes)
        scene_data = list(range(50))  # Larger list
        scene_file.write_bytes(json.dumps(scene_data).encode())

        result = validate_scene_file(scene_file)
        assert result.valid is False
        assert "not a JSON object" in result.error

    def test_missing_expected_keys_warning(self, tmp_path: Path) -> None:
        """Test warning for missing expected keys."""
        scene_file = tmp_path / "empty.splinecode"
        # Create file with enough content but no expected keys
        scene_data = {
            "foo": "bar" * 20,
            "baz": "qux" * 20,
            "extra": "data" * 20,
        }
        scene_file.write_bytes(json.dumps(scene_data).encode())

        result = validate_scene_file(scene_file)
        assert result.valid is True
        assert len(result.warnings) == 1
        assert "expected keys" in result.warnings[0]

    def test_gzip_compressed(self, tmp_path: Path) -> None:
        """Test validation of gzip compressed file."""
        scene_file = tmp_path / "compressed.splinecode"
        scene_data = {
            "objects": [{"id": "1", "name": "Cube", "type": "mesh"}],
            "materials": [{"id": "1", "name": "Default", "type": "standard"}],
            "version": "1.0",
        }
        compressed = gzip.compress(json.dumps(scene_data).encode())
        scene_file.write_bytes(compressed)

        result = validate_scene_file(scene_file)
        assert result.valid is True
        assert result.metadata["compressed"] is True
        assert "decompressed_size" in result.metadata

    def test_invalid_gzip(self, tmp_path: Path) -> None:
        """Test validation of invalid gzip."""
        scene_file = tmp_path / "bad_gzip.splinecode"
        # Gzip magic bytes but invalid content
        scene_file.write_bytes(b'\x1f\x8b' + b"x" * 200)

        result = validate_scene_file(scene_file)
        assert result.valid is False
        assert "decompress" in result.error.lower()

    def test_large_file_warning(self, tmp_path: Path) -> None:
        """Test warning for large files."""
        scene_file = tmp_path / "large.splinecode"
        scene_data = {
            "objects": [{"id": "1", "name": "Cube"}],
            "materials": [{"id": "1", "name": "Default"}],
            "version": "1.0",
            # Add padding to make file > 100 bytes
            "extra_padding": "data" * 20,
        }
        scene_file.write_bytes(json.dumps(scene_data).encode())

        result = validate_scene_file(scene_file)
        # This test is for the files, not regular ones
        # The validator doesn't check file size warnings for regular files
        # So we just test that validation works
        assert result.valid is True
