"""Helper utility MCP tools."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from spline_mcp.assets.manager import SplineAssetManager
from spline_mcp.config import get_logger_instance
from spline_mcp.generators.base import EVENT_TYPE_DOCS, SplineEventType, get_event_documentation

logger = get_logger_instance("spline-mcp.tools.helpers")


def register_helper_tools(app: FastMCP) -> None:
    """Register helper utility tools."""

    @app.tool()
    async def build_export_url(scene_id: str) -> dict[str, str]:
        """Build Spline export URL from scene ID.

        Args:
            scene_id: The scene identifier

        Returns:
            Full export URL
        """
        url = SplineAssetManager.build_export_url(scene_id)

        return {
            "scene_id": scene_id,
            "export_url": url,
            "cdn_url": url,
        }

    @app.tool()
    async def parse_scene_url(url: str) -> dict[str, Any]:
        """Parse Spline URL to extract components.

        Args:
            url: Spline scene URL

        Returns:
            Parsed URL components
        """
        try:
            scene_id = SplineAssetManager.extract_scene_id(url)

            return {
                "success": True,
                "original_url": url,
                "scene_id": scene_id,
                "export_url": SplineAssetManager.build_export_url(scene_id),
            }

        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "original_url": url,
            }

    @app.tool()
    async def list_event_types() -> dict[str, Any]:
        """List all supported Spline event types.

        Returns:
            List of event types with descriptions
        """
        events = [
            {
                "type": event.value,
                "description": get_event_documentation(event),
            }
            for event in SplineEventType
        ]

        return {
            "events": events,
            "total": len(events),
        }

    @app.tool()
    async def get_event_documentation(event_type: str) -> dict[str, Any]:
        """Get documentation for a specific event type.

        Args:
            event_type: Type of event

        Returns:
            Event documentation
        """
        try:
            event = SplineEventType(event_type)
            doc = get_event_documentation(event)

            return {
                "event_type": event.value,
                "description": doc,
                "valid": True,
            }

        except ValueError:
            valid = [e.value for e in SplineEventType]
            return {
                "event_type": event_type,
                "description": "Unknown event type",
                "valid": False,
                "valid_types": valid,
            }

    @app.tool()
    async def generate_snippet(
        snippet_type: str,
        language: str = "typescript",
    ) -> dict[str, Any]:
        """Generate common code snippet.

        Args:
            snippet_type: Type of snippet (load_scene, event_listener, variable_set, transition)
            language: Target language (typescript, javascript)

        Returns:
            Generated code snippet
        """
        snippets = {
            "load_scene": {
                "typescript": """const spline = new Application(canvas);
await spline.load('https://prod.spline.design/SCENE_ID/scene.splinecode');

// Access objects
const cube = spline.findObjectByName('Cube');
console.log(cube);""",
                "javascript": """const spline = new Application(canvas);
await spline.load('https://prod.spline.design/SCENE_ID/scene.splinecode');

// Access objects
const cube = spline.findObjectByName('Cube');
console.log(cube);""",
            },
            "event_listener": {
                "typescript": """spline.addEventListener('mouseDown', (e: SplineEvent) => {
  console.log('Clicked:', e.target.name);

  // Trigger animation
  e.target.emitEvent('mouseHover');
});""",
                "javascript": """spline.addEventListener('mouseDown', (e) => {
  console.log('Clicked:', e.target.name);

  // Trigger animation
  e.target.emitEvent('mouseHover');
});""",
            },
            "variable_set": {
                "typescript": """// Set single variable
spline.setVariable('myColor', '#ff0000');

// Set multiple variables
spline.setVariables({
  color: '#ff0000',
  speed: 2.5,
  visible: true
});""",
                "javascript": """// Set single variable
spline.setVariable('myColor', '#ff0000');

// Set multiple variables
spline.setVariables({
  color: '#ff0000',
  speed: 2.5,
  visible: true
});""",
            },
            "transition": {
                "typescript": """import { Easing } from '@splinetool/runtime';

const obj = spline.findObjectByName('Cube');

// Transition to state
obj.transition({
  to: 'State2',
  duration: 1000,
  easing: Easing.LINEAR
});""",
                "javascript": """import { Easing } from '@splinetool/runtime';

const obj = spline.findObjectByName('Cube');

// Transition to state
obj.transition({
  to: 'State2',
  duration: 1000,
  easing: Easing.LINEAR
});""",
            },
        }

        if snippet_type not in snippets:
            return {
                "success": False,
                "error": f"Unknown snippet type: {snippet_type}",
                "valid_types": list(snippets.keys()),
            }

        code = snippets[snippet_type].get(language, snippets[snippet_type]["typescript"])

        return {
            "success": True,
            "snippet_type": snippet_type,
            "language": language,
            "code": code,
        }


__all__ = ["register_helper_tools"]
