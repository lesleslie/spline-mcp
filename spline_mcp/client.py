"""Spline scene utilities - replaces REST client with asset-focused approach.

This module provides utilities for working with Spline scenes.
Spline does not have a traditional REST API - scenes are managed through:
1. The Spline editor (https://app.spline.design)
2. Code export to .splinecode files
3. The @splinetool/runtime client-side JavaScript library
"""

from __future__ import annotations

from spline_mcp.assets.manager import SplineAssetManager, SceneMetadata
from spline_mcp.assets.validator import ValidationResult, validate_scene_file

# Re-export for backwards compatibility
__all__ = [
    "SplineAssetManager",
    "SceneMetadata",
    "ValidationResult",
    "validate_scene_file",
]
