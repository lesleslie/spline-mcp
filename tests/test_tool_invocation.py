"""Unit tests that exercise the actual tool functions registered on a FastMCP app.

The ``register_*_tools`` functions in ``spline_mcp/tools/*`` register closures
as MCP tools. The closures delegate to existing generators / asset manager /
WebSocket client code that has its own dedicated tests. This file exercises
the closures directly (via ``FastMCP.tool_manager._tools[name].fn``) so the
tool wrapper logic — input normalization, output shape, error handling —
is covered.

The intent is **not** to re-test the generators, but to lift coverage on the
otherwise untested tool wrapper layer (e.g. URL normalization, framework
selection, error payload construction, the helpers' snippet templates).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import FastMCP

from spline_mcp.assets.manager import SplineAssetManager
from spline_mcp.config import get_settings
from spline_mcp.tools.assets import register_asset_tools
from spline_mcp.tools.docs import register_docs_tools
from spline_mcp.tools.generation import register_generation_tools
from spline_mcp.tools.helpers import register_helper_tools
from spline_mcp.tools.integration import register_integration_tools


async def _get_tool_fn(app: FastMCP, name: str):
    """Return the wrapped function for a registered FastMCP tool."""
    tool = await app.get_tool(name)
    return tool.fn


def _make_app(profile_groups: tuple[str, ...] = ()) -> FastMCP:
    """Build a FastMCP app with the listed tool groups registered."""
    app = FastMCP(name="test-invoke")

    register_generation_tools(app)
    register_asset_tools(app)
    register_helper_tools(app)
    register_integration_tools(app)
    register_docs_tools(app)
    return app


# ---------------------------------------------------------------------------
# helpers (build_export_url, parse_scene_url, list_event_types,
#          get_event_documentation, generate_snippet)
# ---------------------------------------------------------------------------
class TestHelperToolInvocations:
    """Exercise the helpers group closures."""

    @pytest.fixture(autouse=True)
    async def _setup(self) -> None:
        self.app = _make_app()
        self.build_export_url = await _get_tool_fn(self.app, "build_export_url")
        self.parse_scene_url = await _get_tool_fn(self.app, "parse_scene_url")
        self.list_event_types = await _get_tool_fn(self.app, "list_event_types")
        self.get_event_documentation = await _get_tool_fn(
            self.app, "get_event_documentation"
        )
        self.generate_snippet = await _get_tool_fn(self.app, "generate_snippet")

    @pytest.mark.asyncio
    async def test_build_export_url_shape(self) -> None:
        """build_export_url returns scene_id, export_url, cdn_url."""
        result = await self.build_export_url(scene_id="abc123")
        assert result["scene_id"] == "abc123"
        assert result["export_url"] == (
            "https://prod.spline.design/abc123/scene.splinecode"
        )
        assert result["cdn_url"] == result["export_url"]

    @pytest.mark.asyncio
    async def test_parse_scene_url_success(self) -> None:
        """parse_scene_url returns success=True with derived export_url."""
        result = await self.parse_scene_url(
            url="https://prod.spline.design/scene-xyz/scene.splinecode"
        )
        assert result["success"] is True
        assert result["scene_id"] == "scene-xyz"
        assert result["original_url"].startswith("https://")
        assert result["export_url"].endswith("/scene.splinecode")

    @pytest.mark.asyncio
    async def test_parse_scene_url_failure(self) -> None:
        """parse_scene_url returns success=False when no scene id is extractable."""
        result = await self.parse_scene_url(url="https://example.com/short")
        assert result["success"] is False
        assert "Could not extract" in result["error"]
        assert result["original_url"] == "https://example.com/short"

    @pytest.mark.asyncio
    async def test_list_event_types_enumeration(self) -> None:
        """list_event_types enumerates every SplineEventType with docs."""
        from spline_mcp.generators.base import SplineEventType

        result = await self.list_event_types()
        assert result["total"] == len(list(SplineEventType))
        names = {e["type"] for e in result["events"]}
        assert names == {e.value for e in SplineEventType}
        for entry in result["events"]:
            assert entry["description"] != ""

    @pytest.mark.asyncio
    async def test_get_event_documentation_valid(self) -> None:
        """get_event_documentation returns valid=True for known event types."""
        result = await self.get_event_documentation(event_type="mouseDown")
        assert result["valid"] is True
        assert result["event_type"] == "mouseDown"
        assert result["description"]

    @pytest.mark.asyncio
    async def test_get_event_documentation_invalid(self) -> None:
        """get_event_documentation returns valid=False for unknown event types."""
        result = await self.get_event_documentation(event_type="notAnEvent")
        assert result["valid"] is False
        assert result["event_type"] == "notAnEvent"
        assert "Unknown event type" in result["description"]
        assert "mouseDown" in result["valid_types"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("snippet_type", "expected_anchor"),
        [
            ("load_scene", "spline.load"),
            ("event_listener", "addEventListener"),
            ("variable_set", "setVariables"),
            ("transition", "transition"),
        ],
    )
    async def test_generate_snippet_typescript(
        self, snippet_type: str, expected_anchor: str
    ) -> None:
        """generate_snippet returns non-empty TypeScript code for each type."""
        result = await self.generate_snippet(
            snippet_type=snippet_type, language="typescript"
        )
        assert result["success"] is True
        assert result["language"] == "typescript"
        assert expected_anchor in result["code"]

    @pytest.mark.asyncio
    async def test_generate_snippet_javascript(self) -> None:
        """generate_snippet returns JavaScript variant when requested."""
        result = await self.generate_snippet(
            snippet_type="load_scene", language="javascript"
        )
        assert result["success"] is True
        assert result["language"] == "javascript"

    @pytest.mark.asyncio
    async def test_generate_snippet_unknown_language_falls_back(self) -> None:
        """Unknown language falls back to typescript code."""
        result = await self.generate_snippet(
            snippet_type="load_scene", language="brainfuck"
        )
        assert result["success"] is True
        assert result["language"] == "brainfuck"
        assert "spline.load" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_snippet_invalid_type(self) -> None:
        """Invalid snippet type returns success=False with valid_types list."""
        result = await self.generate_snippet(snippet_type="notReal")
        assert result["success"] is False
        assert "Unknown snippet type" in result["error"]
        assert "load_scene" in result["valid_types"]


# ---------------------------------------------------------------------------
# docs (get_runtime_api_docs, get_installation_guide,
#       get_troubleshooting_guide)
# ---------------------------------------------------------------------------
class TestDocsToolInvocations:
    """Exercise the docs group closures."""

    @pytest.fixture(autouse=True)
    async def _setup(self) -> None:
        self.app = _make_app()
        self.get_runtime_api_docs = await _get_tool_fn(
            self.app, "get_runtime_api_docs"
        )
        self.get_installation_guide = await _get_tool_fn(
            self.app, "get_installation_guide"
        )
        self.get_troubleshooting_guide = await _get_tool_fn(
            self.app, "get_troubleshooting_guide"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "topic",
        [
            "overview",
            "loading",
            "objects",
            "events",
            "variables",
            "transitions",
            "camera",
            "materials",
        ],
    )
    async def test_get_runtime_api_docs_topics(self, topic: str) -> None:
        """Every documented topic returns a non-empty payload."""
        result = await self.get_runtime_api_docs(topic=topic)
        assert isinstance(result, dict)
        assert "title" in result or "note" in result or "error" not in result
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_get_runtime_api_docs_unknown_topic(self) -> None:
        """Unknown topics fall through the ``.get(topic, ...)`` error path."""
        result = await self.get_runtime_api_docs(topic="unknown_thing")  # type: ignore[arg-type]
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("framework", ["react", "nextjs", "vue", "vanilla"])
    async def test_get_installation_guide_frameworks(
        self, framework: str
    ) -> None:
        """All four frameworks return an installation guide dict."""
        result = await self.get_installation_guide(framework=framework)
        assert isinstance(result, dict)
        assert "title" in result
        assert "npm" in result or "cdn" in result

    @pytest.mark.asyncio
    async def test_get_installation_guide_unknown_framework(self) -> None:
        """Unknown framework returns an error payload."""
        result = await self.get_installation_guide(framework="alpine")  # type: ignore[arg-type]
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "issue",
        [
            "scene_not_loading",
            "cors_error",
            "objects_not_found",
            "variables_not_working",
        ],
    )
    async def test_get_troubleshooting_guide_issues(self, issue: str) -> None:
        """Each issue key returns a troubleshooting payload."""
        result = await self.get_troubleshooting_guide(issue=issue)
        assert "title" in result
        assert "checks" in result or "solutions" in result

    @pytest.mark.asyncio
    async def test_get_troubleshooting_guide_unknown_issue(self) -> None:
        """Unknown issue returns an error payload."""
        result = await self.get_troubleshooting_guide(issue="mystery")  # type: ignore[arg-type]
        assert "error" in result


# ---------------------------------------------------------------------------
# generation (generate_react_component, generate_vanilla_js,
#             generate_nextjs_component, generate_event_handler,
#             generate_variable_binding, generate_full_integration)
# ---------------------------------------------------------------------------
class TestGenerationToolInvocations:
    """Exercise the generation group closures."""

    @pytest.fixture(autouse=True)
    async def _setup(self) -> None:
        get_settings.cache_clear()
        self.app = _make_app()
        self.generate_react_component = await _get_tool_fn(
            self.app, "generate_react_component"
        )
        self.generate_vanilla_js = await _get_tool_fn(
            self.app, "generate_vanilla_js"
        )
        self.generate_nextjs_component = await _get_tool_fn(
            self.app, "generate_nextjs_component"
        )
        self.generate_event_handler = await _get_tool_fn(
            self.app, "generate_event_handler"
        )
        self.generate_variable_binding = await _get_tool_fn(
            self.app, "generate_variable_binding"
        )
        self.generate_full_integration = await _get_tool_fn(
            self.app, "generate_full_integration"
        )

    @pytest.mark.asyncio
    async def test_generate_react_component_bare_id(self) -> None:
        """Bare scene IDs are normalized to a prod.spline.design URL."""
        result = await self.generate_react_component(
            scene_url="bare-id-12345",
            component_name="MyScene",
        )
        assert result["framework"] == "react"
        assert result["component_name"] == "MyScene"
        assert "prod.spline.design/bare-id-12345/scene.splinecode" in result["code"]
        assert "npm install" in result["install_command"]

    @pytest.mark.asyncio
    async def test_generate_react_component_with_websocket(self) -> None:
        """include_websocket=True emits the useWebSocket hook."""
        result = await self.generate_react_component(
            scene_url="abc123",
            include_websocket=True,
            websocket_url="ws://test:1234",
        )
        assert "useWebSocket" in result["code"]
        assert "ws://test:1234" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_vanilla_js_includes_runtime(self) -> None:
        """Vanilla JS output includes the runtime import and DOCTYPE."""
        result = await self.generate_vanilla_js(scene_url="abc123")
        assert result["framework"] == "vanilla"
        assert "<!DOCTYPE html>" in result["code"]
        assert "Application" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_nextjs_component(self) -> None:
        """Next.js output includes 'use client' and dynamic import."""
        result = await self.generate_nextjs_component(scene_url="abc123")
        assert result["framework"] == "nextjs"
        assert "use client" in result["code"]
        assert "ssr: false" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_event_handler_react(self) -> None:
        """Event handler with valid event_type and React framework."""
        result = await self.generate_event_handler(
            event_type="mouseDown",
            handler_code="console.log('clicked')",
            target_object="Cube",
            framework="react",
        )
        assert result["framework"] == "react"
        assert result["event_type"] == "mouseDown"
        assert "Cube" in result["code"]
        assert "mouseDown" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_event_handler_vanilla(self) -> None:
        """Event handler with vanilla framework selects VanillaJSGenerator."""
        result = await self.generate_event_handler(
            event_type="mouseUp", framework="vanilla"
        )
        assert result["framework"] == "vanilla"
        assert "addEventListener" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_event_handler_nextjs(self) -> None:
        """Event handler with nextjs framework selects NextJSGenerator."""
        result = await self.generate_event_handler(
            event_type="mouseHover", framework="nextjs"
        )
        assert result["framework"] == "nextjs"
        assert "mouseHover" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_event_handler_invalid_event(self) -> None:
        """Invalid event_type returns an error payload (no exception)."""
        result = await self.generate_event_handler(event_type="notReal")
        assert "error" in result
        assert "valid_types" in result
        assert "mouseDown" in result["valid_types"]

    @pytest.mark.asyncio
    async def test_generate_variable_binding(self) -> None:
        """Variable binding generates a dictionary literal."""
        result = await self.generate_variable_binding(
            variables={"color": "#ff0000", "speed": 2.5},
            framework="react",
        )
        assert result["framework"] == "react"
        assert "color" in result["code"]
        assert "speed" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_variable_binding_nextjs(self) -> None:
        """Variable binding nextjs framework path."""
        result = await self.generate_variable_binding(
            variables={"x": 1}, framework="nextjs"
        )
        assert result["framework"] == "nextjs"
        assert "x" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_variable_binding_vanilla(self) -> None:
        """Variable binding vanilla framework path."""
        result = await self.generate_variable_binding(
            variables={"x": 1}, framework="vanilla"
        )
        assert result["framework"] == "vanilla"
        assert "x" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_full_integration_react(self) -> None:
        """generate_full_integration (react) emits install + usage + features."""
        result = await self.generate_full_integration(
            scene_url="abc123",
            framework="react",
            component_name="FullScene",
            event_handlers=[
                {
                    "event_type": "mouseDown",
                    "handler_code": "console.log('clicked')",
                    "target_object": "Cube",
                }
            ],
            variables={"color": "#ff0000"},
            include_websocket=True,
        )
        assert result["framework"] == "react"
        assert "FullScene" in result["code"]
        assert result["features"]["event_handlers"] == 1
        assert result["features"]["variables"] == 1
        assert result["features"]["websocket"] is True

    @pytest.mark.asyncio
    async def test_generate_full_integration_nextjs(self) -> None:
        """generate_full_integration (nextjs) emits 'use client'."""
        result = await self.generate_full_integration(
            scene_url="abc123",
            framework="nextjs",
            component_name="NextFull",
        )
        assert result["framework"] == "nextjs"
        assert "use client" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_full_integration_vanilla(self) -> None:
        """generate_full_integration (vanilla) emits the HTML wrapper."""
        result = await self.generate_full_integration(
            scene_url="abc123",
            framework="vanilla",
        )
        assert result["framework"] == "vanilla"
        assert "<!DOCTYPE html>" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_full_integration_invalid_event_skipped(self) -> None:
        """Invalid event handlers are dropped without raising."""
        result = await self.generate_full_integration(
            scene_url="abc123",
            event_handlers=[
                {"event_type": "notReal"},  # invalid → skipped
                {"event_type": "mouseDown"},
            ],
        )
        assert result["features"]["event_handlers"] == 1

    @pytest.mark.asyncio
    async def test_generate_full_integration_normalizes_url(self) -> None:
        """Bare scene IDs are normalized to the prod.spline.design URL."""
        result = await self.generate_full_integration(
            scene_url="abc123", framework="react"
        )
        assert "prod.spline.design/abc123/scene.splinecode" in result["code"]


# ---------------------------------------------------------------------------
# assets (download_scene, validate_scene, list_cached_scenes,
#         clear_cache, get_cache_stats)
# ---------------------------------------------------------------------------
class TestAssetToolInvocations:
    """Exercise the asset group closures."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        get_settings.cache_clear()
        self.tmpdir = tempfile.mkdtemp()
        self.settings = get_settings()
        self.settings.cache_dir = Path(self.tmpdir)
        self.app = self._make_app_with_settings()
        self.validate_scene = None  # resolved per-test for clarity

    def _make_app_with_settings(self) -> FastMCP:
        """Register tools against a temp cache_dir."""
        app = FastMCP(name="test-assets")
        register_asset_tools(app)
        return app

    @pytest.mark.asyncio
    async def test_validate_scene_local(self) -> None:
        """validate_scene(scene_path=...) delegates to validate_scene_file."""
        scene_file = Path(self.tmpdir) / "abc123.splinecode"
        scene_file.write_bytes(
            json.dumps(
                {
                    "objects": [{"name": "Cube"}],
                    "materials": [{"name": "Default"}],
                    "version": "1.0",
                }
            ).encode().ljust(200, b" ")
        )

        fn = await _get_tool_fn(self.app, "validate_scene")

        with patch("spline_mcp.tools.assets.get_settings", return_value=self.settings):
            result = await fn(scene_path=str(scene_file))

        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_scene_neither(self) -> None:
        """validate_scene() with neither arg returns valid=False error."""
        fn = await _get_tool_fn(self.app, "validate_scene")
        result = await fn()
        assert result["valid"] is False
        assert "Either" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_scene_url(self) -> None:
        """validate_scene(scene_url=...) downloads then validates."""
        fn = await _get_tool_fn(self.app, "validate_scene")

        scene_file = Path(self.tmpdir) / "abc123.splinecode"
        scene_file.write_bytes(
            json.dumps(
                {
                    "objects": [{"name": "Cube"}],
                    "materials": [{"name": "Default"}],
                    "version": "1.0",
                }
            ).encode().ljust(200, b" ")
        )

        with patch("spline_mcp.tools.assets.get_settings", return_value=self.settings):
            result = await fn(
                scene_url="https://prod.spline.design/abc123/scene.splinecode"
            )

        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_download_scene_uses_cache(self) -> None:
        """download_scene returns success=True when file is already cached."""
        scene_file = Path(self.tmpdir) / "abc123.splinecode"
        scene_file.write_text(
            json.dumps(
                {
                    "objects": [{"name": "Cube"}],
                    "materials": [{"name": "Default"}],
                }
            ).ljust(200, " ")
        )

        fn = await _get_tool_fn(self.app, "download_scene")
        with patch("spline_mcp.tools.assets.get_settings", return_value=self.settings):
            result = await fn(
                scene_url="https://prod.spline.design/abc123/scene.splinecode"
            )

        assert result["success"] is True
        assert result["scene_id"] == "abc123"
        assert result["local_url"] == "/assets/spline/abc123.splinecode"

    @pytest.mark.asyncio
    async def test_download_scene_failure(self) -> None:
        """download_scene returns success=False when manager raises."""
        fn = await _get_tool_fn(self.app, "download_scene")

        with patch("spline_mcp.tools.assets.get_settings", return_value=self.settings):
            with patch.object(
                SplineAssetManager, "download_scene", side_effect=RuntimeError("boom")
            ):
                result = await fn(
                    scene_url="https://prod.spline.design/abc123/scene.splinecode"
                )

        assert result["success"] is False
        assert "boom" in result["error"]

    @pytest.mark.asyncio
    async def test_list_cached_scenes(self) -> None:
        """list_cached_scenes returns metadata + cache_stats for each entry."""
        scene_file = Path(self.tmpdir) / "abc123.splinecode"
        scene_file.write_text(
            json.dumps({"objects": [], "materials": []}).ljust(200, " ")
        )

        fn = await _get_tool_fn(self.app, "list_cached_scenes")
        with patch("spline_mcp.tools.assets.get_settings", return_value=self.settings):
            result = await fn()

        assert result["total"] == 1
        assert result["scenes"][0]["scene_id"] == "abc123"
        assert "cache_stats" in result

    @pytest.mark.asyncio
    async def test_clear_cache_all(self) -> None:
        """clear_cache() with no scene_id clears every cached file."""
        scene_file = Path(self.tmpdir) / "abc123.splinecode"
        scene_file.write_bytes(b"data")

        fn = await _get_tool_fn(self.app, "clear_cache")
        with patch("spline_mcp.tools.assets.get_settings", return_value=self.settings):
            result = await fn()

        assert result["cleared"] == 1

    @pytest.mark.asyncio
    async def test_clear_cache_specific(self) -> None:
        """clear_cache(scene_id=...) only removes the specified file."""
        (Path(self.tmpdir) / "abc123.splinecode").write_bytes(b"data")
        (Path(self.tmpdir) / "def456.splinecode").write_bytes(b"data")

        fn = await _get_tool_fn(self.app, "clear_cache")
        with patch("spline_mcp.tools.assets.get_settings", return_value=self.settings):
            result = await fn(scene_id="abc123")

        assert result["cleared"] == 1

    @pytest.mark.asyncio
    async def test_get_cache_stats(self) -> None:
        """get_cache_stats returns size + count + utilization."""
        fn = await _get_tool_fn(self.app, "get_cache_stats")
        with patch("spline_mcp.tools.assets.get_settings", return_value=self.settings):
            result = await fn()

        assert result["file_count"] == 0
        assert result["cache_dir"] == self.tmpdir


# ---------------------------------------------------------------------------
# integration (get_websocket_status, subscribe_to_channel,
#              get_integration_status)
# ---------------------------------------------------------------------------
class TestIntegrationToolInvocations:
    """Exercise the integration group closures."""

    @pytest.fixture(autouse=True)
    async def _setup(self) -> None:
        get_settings.cache_clear()
        self.app = _make_app()
        self.get_websocket_status = await _get_tool_fn(
            self.app, "get_websocket_status"
        )
        self.subscribe_to_channel = await _get_tool_fn(
            self.app, "subscribe_to_channel"
        )
        self.get_integration_status = await _get_tool_fn(
            self.app, "get_integration_status"
        )

    @pytest.mark.asyncio
    async def test_get_websocket_status_disabled(self) -> None:
        """get_websocket_status returns enabled=False when settings disabled."""
        settings = get_settings()
        settings.websocket_enabled = False
        with patch(
            "spline_mcp.tools.integration.get_settings", return_value=settings
        ):
            result = await self.get_websocket_status()
        assert result["enabled"] is False
        assert "disabled" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_get_websocket_status_enabled_no_connect(self) -> None:
        """get_websocket_status with enabled but unreachable host."""
        settings = get_settings()
        settings.websocket_enabled = True
        settings.websocket_url = "ws://127.0.0.1:1"
        with patch(
            "spline_mcp.tools.integration.get_settings", return_value=settings
        ):
            result = await self.get_websocket_status()
        assert result["enabled"] is True
        # Client falls back to ERROR status without raising

    @pytest.mark.asyncio
    async def test_subscribe_to_channel_disabled(self) -> None:
        """subscribe_to_channel returns success=False when websocket disabled."""
        settings = get_settings()
        settings.websocket_enabled = False
        with patch(
            "spline_mcp.tools.integration.get_settings", return_value=settings
        ):
            result = await self.subscribe_to_channel(channel="spline:vars")
        assert result["success"] is False
        assert "disabled" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_subscribe_to_channel_not_connected(self) -> None:
        """subscribe_to_channel returns success=False when not connected."""
        settings = get_settings()
        settings.websocket_enabled = True
        with patch(
            "spline_mcp.tools.integration.get_settings", return_value=settings
        ):
            with patch(
                "spline_mcp.tools.integration._websocket_client", None
            ):
                # Force the lazy getter to instantiate a fresh client
                with patch(
                    "spline_mcp.tools.integration.get_websocket_client"
                ) as mock_client:
                    client = MagicMock()
                    client.is_connected = False
                    client.status.value = "disconnected"
                    mock_client.return_value = client
                    result = await self.subscribe_to_channel(channel="c")
        assert result["success"] is False
        assert result["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_get_integration_status_disabled(self) -> None:
        """get_integration_status with websocket disabled reports enabled=False."""
        settings = get_settings()
        settings.websocket_enabled = False
        settings.websocket_url = "ws://localhost:8690"
        with patch(
            "spline_mcp.tools.integration.get_settings", return_value=settings
        ):
            result = await self.get_integration_status()
        assert result["websocket"]["enabled"] is False
        assert result["websocket"]["url"] == "ws://localhost:8690"

    @pytest.mark.asyncio
    async def test_get_integration_status_enabled(self) -> None:
        """get_integration_status with websocket enabled reports status."""
        settings = get_settings()
        settings.websocket_enabled = True
        settings.websocket_url = "ws://localhost:8690"
        with patch(
            "spline_mcp.tools.integration.get_settings", return_value=settings
        ):
            with patch(
                "spline_mcp.tools.integration.get_websocket_client"
            ) as mock_client:
                client = MagicMock()
                client.status.value = "disconnected"
                client.is_connected = False
                mock_client.return_value = client
                result = await self.get_integration_status()
        assert result["websocket"]["enabled"] is True
        assert result["websocket"]["status"] == "disconnected"
        assert result["websocket"]["connected"] is False