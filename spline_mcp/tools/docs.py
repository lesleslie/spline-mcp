"""Documentation MCP tools for Spline runtime API."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP

from spline_mcp.config import get_logger_instance

logger = get_logger_instance("spline-mcp.tools.docs")


def register_docs_tools(app: FastMCP) -> None:
    """Register documentation tools."""

    @app.tool()
    async def get_runtime_api_docs(
        topic: Literal[
            "overview",
            "loading",
            "objects",
            "events",
            "variables",
            "transitions",
            "camera",
            "materials",
        ] = "overview",
    ) -> dict[str, Any]:
        """Get documentation for @splinetool/runtime API.

        Args:
            topic: Specific topic to get documentation for

        Returns:
            Documentation for the requested topic
        """
        docs = {
            "overview": {
                "title": "@splinetool/runtime Overview",
                "description": "Client-side JavaScript library for running Spline scenes",
                "npm_package": "@splinetool/runtime",
                "cdn_url": "https://unpkg.com/@splinetool/runtime/build/runtime.js",
                "basic_usage": "import { Application } from '@splinetool/runtime';\nconst spline = new Application(canvas);\nawait spline.load(url);",
                "key_features": [
                    "Load .splinecode scenes",
                    "Find and manipulate objects",
                    "Event handling",
                    "Runtime variables",
                    "State transitions",
                ],
            },
            "loading": {
                "title": "Scene Loading",
                "methods": ["load(url)", "load(url, { variables })"],
                "example": "await spline.load('https://prod.spline.design/xxx/scene.splinecode');",
            },
            "objects": {
                "title": "Object Management",
                "methods": [
                    "findObjectByName(name)",
                    "findObjectById(id)",
                    "getAllObjects()",
                ],
                "properties": ["position", "rotation", "scale", "visible"],
            },
            "events": {
                "title": "Event Handling",
                "event_types": ["mouseDown", "mouseUp", "mouseHover", "keyDown", "keyUp", "scroll"],
                "methods": ["addEventListener(type, callback)", "emitEvent(type)"],
            },
            "variables": {
                "title": "Runtime Variables",
                "methods": ["setVariable(name, value)", "setVariables(obj)", "getVariable(name)"],
            },
            "transitions": {
                "title": "State Transitions",
                "methods": ["transition({ to, duration, easing })"],
                "easing": ["LINEAR", "EASE_IN", "EASE_OUT", "EASE_IN_OUT"],
            },
            "camera": {
                "title": "Camera Control",
                "methods": ["setCameraPosition(x, y, z)", "setCameraTarget(x, y, z)"],
            },
            "materials": {
                "title": "Materials",
                "note": "Materials typically set in editor, can be modified via variables",
            },
        }
        return docs.get(topic, {"error": f"Unknown topic: {topic}"})

    @app.tool()
    async def get_installation_guide(
        framework: Literal["react", "nextjs", "vue", "vanilla"] = "react",
    ) -> dict[str, Any]:
        """Get installation guide for Spline in different frameworks.

        Args:
            framework: Target framework

        Returns:
            Installation instructions
        """
        guides = {
            "react": {
                "title": "React Installation",
                "npm": "npm install @splinetool/react-spline",
                "basic": "<Spline scene='https://prod.spline.design/xxx/scene.splinecode' />",
            },
            "nextjs": {
                "title": "Next.js Installation",
                "npm": "npm install @splinetool/react-spline",
                "note": "Use dynamic import with ssr: false",
            },
            "vue": {
                "title": "Vue Installation",
                "npm": "npm install @splinetool/runtime",
                "note": "Use directly in component",
            },
            "vanilla": {
                "title": "Vanilla JS Installation",
                "cdn": "https://unpkg.com/@splinetool/runtime/build/runtime.js",
                "npm": "npm install @splinetool/runtime",
            },
        }
        return guides.get(framework, {"error": f"Unknown framework: {framework}"})

    @app.tool()
    async def get_troubleshooting_guide(
        issue: Literal[
            "scene_not_loading",
            "cors_error",
            "objects_not_found",
            "variables_not_working",
        ],
    ) -> dict[str, Any]:
        """Get troubleshooting guidance for common Spline issues.

        Args:
            issue: Type of issue encountered

        Returns:
            Troubleshooting steps
        """
        guides = {
            "scene_not_loading": {
                "title": "Scene Not Loading",
                "checks": [
                    "Verify URL ends with /scene.splinecode",
                    "Check network tab for errors",
                    "Verify scene is published",
                ],
            },
            "cors_error": {
                "title": "CORS Error",
                "solutions": [
                    "Download and self-host the .splinecode file",
                    "Use spline-mcp download command",
                ],
            },
            "objects_not_found": {
                "title": "Objects Not Found",
                "checks": [
                    "Names are case-sensitive",
                    "Wait for onLoad callback",
                    "Use getAllObjects() to debug",
                ],
            },
            "variables_not_working": {
                "title": "Variables Not Working",
                "checks": [
                    "Variable must exist in Spline editor",
                    "Check name spelling (case-sensitive)",
                    "Verify type matches (string, number, boolean)",
                ],
            },
        }
        return guides.get(issue, {"error": f"Unknown issue: {issue}"})


__all__ = ["register_docs_tools"]
