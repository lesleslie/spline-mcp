"""Scene file validation."""

from __future__ import annotations

import gzip
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of scene file validation."""

    valid: bool
    file_size: int = 0
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "file_size": self.file_size,
            "error": self.error,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


def validate_scene_file(path: Path) -> ValidationResult:
    """Validate a .splinecode file.

    Args:
        path: Path to the .splinecode file

    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(valid=True)

    if not path.exists():
        return ValidationResult(
            valid=False,
            error=f"File not found: {path}",
        )

    if not path.is_file():
        return ValidationResult(
            valid=False,
            error=f"Not a file: {path}",
        )

    try:
        stat = path.stat()
        result.file_size = stat.st_size

        # Check minimum size (should have at least some content)
        if result.file_size < 100:
            return ValidationResult(
                valid=False,
                file_size=result.file_size,
                error="File too small to be a valid .splinecode file",
            )

        # Check maximum size (reasonable limit: 100MB)
        if result.file_size > 100 * 1024 * 1024:
            result.warnings.append("File is unusually large (>100MB)")

        # Read file content
        content = path.read_bytes()

        # Try to detect format
        if content[:2] == b'\x1f\x8b':
            # Gzip compressed
            result.metadata["compressed"] = True
            try:
                decompressed = gzip.decompress(content)
                result.metadata["decompressed_size"] = len(decompressed)
                _validate_json_content(decompressed, result)
            except Exception as e:
                return ValidationResult(
                    valid=False,
                    file_size=result.file_size,
                    error=f"Failed to decompress gzip content: {e}",
                )
        else:
            # Try as JSON directly
            result.metadata["compressed"] = False
            _validate_json_content(content, result)

    except Exception as e:
        return ValidationResult(
            valid=False,
            error=f"Validation error: {e}",
        )

    return result


def _validate_json_content(content: bytes, result: ValidationResult) -> None:
    """Validate JSON content of scene file.

    Args:
        content: Raw bytes content
        result: ValidationResult to update
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        result.valid = False
        result.error = f"Invalid JSON: {e}"
        return

    # Check for expected Spline scene structure
    if not isinstance(data, dict):
        result.valid = False
        result.error = "Scene data is not a JSON object"
        return

    # Look for common Spline scene properties
    expected_keys = ["objects", "materials", "animations", "states"]
    found_keys = [k for k in expected_keys if k in data]

    if not found_keys:
        result.warnings.append(
            "Scene doesn't contain expected keys (objects, materials, etc.)"
        )
    else:
        result.metadata["scene_keys"] = found_keys

    # Count objects if present
    if "objects" in data and isinstance(data["objects"], list):
        result.metadata["object_count"] = len(data["objects"])

    # Count materials if present
    if "materials" in data and isinstance(data["materials"], list):
        result.metadata["material_count"] = len(data["materials"])

    # Check for version info
    if "version" in data:
        result.metadata["version"] = data["version"]

    result.valid = True


__all__ = ["ValidationResult", "validate_scene_file"]
