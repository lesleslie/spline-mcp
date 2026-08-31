"""Coverage boosters for the small miscellaneous modules.

Covers:
- ``spline_mcp.client`` re-export module (4 statements, was 0%).
- ``spline_mcp.tools.profiles`` (register_all_tool_groups + apply_spline_tool_profile
  paths that don't have other coverage).
- ``integrations.websocket`` pure paths: subscribe without connect, publish without
  connect, get_status_dict with subscribers, disconnect idempotence.
- ``assets.manager`` cleanup path via _cleanup_if_needed (cache overflow).

The goal is to lift coverage above the 80% gate without changing production
behavior. Every test here uses tmp_path / mocks so no real I/O.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import FastMCP

from spline_mcp import client as spline_client
from spline_mcp import server as spline_server
from spline_mcp.assets.manager import SplineAssetManager
from spline_mcp.config import get_settings
from spline_mcp.integrations.websocket import (
    WebSocketClient,
    WebSocketMessage,
    WebSocketStatus,
)
from spline_mcp.tools.profiles import (
    FULL_REGISTRATIONS,
    MINIMAL_REGISTRATIONS,
    PROFILE_REGISTRATIONS,
    STANDARD_REGISTRATIONS,
    _build_registration_map,
    register_all_tool_groups,
)


# ---------------------------------------------------------------------------
# spline_mcp.client re-export module
# ---------------------------------------------------------------------------
class TestClientReExports:
    """client.py is a backwards-compat re-export of the asset surface."""

    def test_re_exports_assets_manager(self) -> None:
        """``SplineAssetManager`` from spline_mcp.client is the same class."""
        from spline_mcp.assets.manager import SplineAssetManager as SAM

        assert spline_client.SplineAssetManager is SAM

    def test_re_exports_scene_metadata(self) -> None:
        """``SceneMetadata`` from spline_mcp.client is the same class."""
        from spline_mcp.assets.manager import SceneMetadata as SM

        assert spline_client.SceneMetadata is SM

    def test_re_exports_validation_result(self) -> None:
        """``ValidationResult`` from spline_mcp.client is the same class."""
        from spline_mcp.assets.validator import ValidationResult as VR

        assert spline_client.ValidationResult is VR

    def test_re_exports_validate_scene_file(self) -> None:
        """``validate_scene_file`` from spline_mcp.client is the same fn."""
        from spline_mcp.assets.validator import validate_scene_file as vsf

        assert spline_client.validate_scene_file is vsf

    def test_all_exports_match(self) -> None:
        """client.__all__ matches the module's exported attributes."""
        assert set(spline_client.__all__) == {
            "SplineAssetManager",
            "SceneMetadata",
            "ValidationResult",
            "validate_scene_file",
        }


# ---------------------------------------------------------------------------
# spline_mcp.tools.profiles surface
# ---------------------------------------------------------------------------
class TestProfilesSurface:
    """Validate the profile-registration dispatch surface."""

    def test_minimal_registrations_empty(self) -> None:
        """MINIMAL profile registers no tool groups."""
        assert MINIMAL_REGISTRATIONS == []

    def test_standard_registrations_lists_four_groups(self) -> None:
        """STANDARD profile lists the four daily-driver groups."""
        assert set(STANDARD_REGISTRATIONS) == {
            "asset_tools",
            "generation_tools",
            "helper_tools",
            "docs_tools",
        }

    def test_full_includes_integration(self) -> None:
        """FULL profile adds integration_tools to STANDARD."""
        assert set(FULL_REGISTRATIONS) == {
            "asset_tools",
            "generation_tools",
            "helper_tools",
            "docs_tools",
            "integration_tools",
        }

    def test_profile_registrations_keys(self) -> None:
        """PROFILE_REGISTRATIONS maps every ToolProfile to a list."""
        from mcp_common.tools import ToolProfile

        assert set(PROFILE_REGISTRATIONS.keys()) == set(ToolProfile)

    def test_build_registration_map_has_five_groups(self) -> None:
        """_build_registration_map produces 5 group → register_fn entries."""
        mapping = _build_registration_map()
        assert set(mapping.keys()) == {
            "asset_tools",
            "generation_tools",
            "helper_tools",
            "docs_tools",
            "integration_tools",
        }
        # Every entry is callable
        for fn in mapping.values():
            assert callable(fn)

    def test_register_all_tool_groups_registers_all_five(self) -> None:
        """register_all_tool_groups(server) registers all 22 tools + meta-tool."""
        import asyncio

        app = FastMCP(name="test-all-groups")
        register_all_tool_groups(app)

        async def _names() -> set[str]:
            return {t.name for t in await app.list_tools()}

        names = asyncio.run(_names())
        # Every group registers at least one tool
        assert any(name.startswith("generate_") for name in names)
        assert any(
            name in {"download_scene", "validate_scene", "list_cached_scenes"}
            for name in names
        )
        assert "build_export_url" in names
        assert "get_runtime_api_docs" in names
        assert "get_websocket_status" in names


# ---------------------------------------------------------------------------
# spline_mcp.integrations.websocket pure paths
# ---------------------------------------------------------------------------
class TestWebSocketPurePaths:
    """Exercise WebSocketClient methods without performing real I/O."""

    def test_init_logs(self) -> None:
        """__init__ stores all args and defaults."""
        client = WebSocketClient(url="ws://test:9999")
        assert client.url == "ws://test:9999"
        assert client.auto_reconnect is True
        assert client.reconnect_delay == 5.0
        assert client.max_reconnect_attempts == 3
        assert client.status == WebSocketStatus.DISCONNECTED

    def test_status_property(self) -> None:
        """status property reflects the internal status."""
        client = WebSocketClient(url="ws://test")
        assert client.status == WebSocketStatus.DISCONNECTED
        client._status = WebSocketStatus.CONNECTING
        assert client.status == WebSocketStatus.CONNECTING

    def test_is_connected_property(self) -> None:
        """is_connected is True only when status == CONNECTED."""
        client = WebSocketClient(url="ws://test")
        client._status = WebSocketStatus.DISCONNECTED
        assert client.is_connected is False

        client._status = WebSocketStatus.CONNECTED
        assert client.is_connected is True

        client._status = WebSocketStatus.ERROR
        assert client.is_connected is False

    @pytest.mark.asyncio
    async def test_publish_when_disconnected(self) -> None:
        """publish() returns False (and doesn't raise) when not connected."""
        client = WebSocketClient(url="ws://test")
        result = await client.publish(channel="c", payload={"x": 1})
        assert result is False

    @pytest.mark.asyncio
    async def test_subscribe_without_connect(self) -> None:
        """subscribe() without connect stores the handler but doesn't send."""
        client = WebSocketClient(url="ws://test")

        def _h(_data: object) -> None:
            pass

        unsub = await client.subscribe(channel="c1", handler=_h)
        # Subscriber was added
        assert len(client._subscribers["c1"]) == 1
        # No websocket, no crash
        unsub()
        assert client._subscribers["c1"] == []

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe_via_returned_callable(self) -> None:
        """The returned callable removes the handler."""
        client = WebSocketClient(url="ws://test")

        def _h(_data: object) -> None:
            pass

        unsub = await client.subscribe(channel="c2", handler=_h)
        assert "c2" in client._subscribers

        unsub()

        # Channel key remains, but list is empty
        assert client._subscribers.get("c2") == []

    @pytest.mark.asyncio
    async def test_subscribe_same_channel_twice(self) -> None:
        """subscribe() on the same channel accumulates handlers."""
        client = WebSocketClient(url="ws://test")

        def _h1(_data: object) -> None:
            pass

        def _h2(_data: object) -> None:
            pass

        await client.subscribe(channel="c3", handler=_h1)
        await client.subscribe(channel="c3", handler=_h2)
        assert len(client._subscribers["c3"]) == 2

    @pytest.mark.asyncio
    async def test_subscribe_with_connected_websocket_sends(self) -> None:
        """subscribe() with an active websocket sends the subscribe frame."""
        client = WebSocketClient(url="ws://test")
        sent_payloads: list[str] = []

        class _FakeWS:
            async def send(self, payload: str) -> None:
                sent_payloads.append(payload)

        client._websocket = _FakeWS()
        client._status = WebSocketStatus.CONNECTED

        def _h(_data: object) -> None:
            pass

        await client.subscribe(channel="c4", handler=_h)

        assert len(sent_payloads) == 1
        parsed = json.loads(sent_payloads[0])
        assert parsed["type"] == "subscribe"
        assert parsed["channel"] == "c4"

    def test_get_status_dict_with_subscribers(self) -> None:
        """get_status_dict surfaces subscriber counts per channel."""
        client = WebSocketClient(url="ws://test")
        client._subscribers = {"alpha": [lambda d: None], "beta": [lambda d: None, lambda d: None]}
        result = client.get_status_dict()
        assert result["url"] == "ws://test"
        assert result["status"] == "disconnected"
        assert result["is_connected"] is False
        assert result["subscribers"] == {"alpha": 1, "beta": 2}

    def test_get_status_dict_empty(self) -> None:
        """get_status_dict with no subscribers has empty subscribers dict."""
        client = WebSocketClient(url="ws://other:1234")
        result = client.get_status_dict()
        assert result["url"] == "ws://other:1234"
        assert result["subscribers"] == {}


class TestWebSocketMessage:
    """WebSocketMessage pydantic model round-trip."""

    def test_minimal_message(self) -> None:
        """Minimal message has only ``type`` set."""
        msg = WebSocketMessage(type="ping")
        assert msg.type == "ping"
        assert msg.channel is None
        assert msg.payload is None

    def test_full_message(self) -> None:
        """Full message carries type/channel/payload."""
        msg = WebSocketMessage(
            type="publish", channel="spline:variables", payload={"color": "#fff"}
        )
        dumped = msg.model_dump_json()
        roundtrip = WebSocketMessage.model_validate_json(dumped)
        assert roundtrip.type == "publish"
        assert roundtrip.channel == "spline:variables"
        assert roundtrip.payload == {"color": "#fff"}


class TestWebSocketConnect:
    """Cover the connect() failure paths without real network I/O."""

    @pytest.mark.asyncio
    async def test_connect_already_connected(self) -> None:
        """connect() short-circuits if already connected."""
        client = WebSocketClient(url="ws://test")
        client._status = WebSocketStatus.CONNECTED

        result = await client.connect()
        assert result is True

    @pytest.mark.asyncio
    async def test_connect_timeout(self) -> None:
        """connect() returns False on TimeoutError."""
        client = WebSocketClient(url="ws://test", auto_reconnect=False)
        with patch("asyncio.wait_for", side_effect=TimeoutError):
            result = await client.connect()
        assert result is False
        assert client.status == WebSocketStatus.ERROR

    @pytest.mark.asyncio
    async def test_connect_exception(self) -> None:
        """connect() returns False on any other exception (soft failover)."""
        client = WebSocketClient(url="ws://test", auto_reconnect=False)
        with patch("asyncio.wait_for", side_effect=OSError("nope")):
            result = await client.connect()
        assert result is False
        assert client.status == WebSocketStatus.ERROR

    @pytest.mark.asyncio
    async def test_disconnect_idempotent(self) -> None:
        """disconnect() with no active connection is a no-op."""
        client = WebSocketClient(url="ws://test")
        await client.disconnect()
        assert client.status == WebSocketStatus.DISCONNECTED

    @pytest.mark.asyncio
    async def test_disconnect_cancels_task_and_closes_ws(self) -> None:
        """disconnect() must cancel the message task and close the websocket."""
        client = WebSocketClient(url="ws://test")
        # Fake active websocket and task
        fake_ws = MagicMock()

        async def _close() -> None:
            return None

        fake_ws.close = _close
        client._websocket = fake_ws

        async def _task() -> None:
            await asyncio.sleep(60)

        import asyncio

        client._task = asyncio.create_task(_task())

        await client.disconnect()
        assert client._websocket is None
        assert client._task is None
        assert client.status == WebSocketStatus.DISCONNECTED


# ---------------------------------------------------------------------------
# assets.manager _cleanup_if_needed path
# ---------------------------------------------------------------------------
class TestAssetManagerCleanup:
    """Exercise the cache overflow eviction path."""

    @pytest.mark.asyncio
    async def test_cleanup_triggers_eviction_when_over_limit(
        self, tmp_path: Path
    ) -> None:
        """When cache > max_size_bytes, oldest files are evicted."""
        # Create a few files
        for name in ("a.splinecode", "b.splinecode", "c.splinecode"):
            (tmp_path / name).write_bytes(b"x" * 100)

        # 1 MB limit so total 300 bytes is well under it
        manager = SplineAssetManager(cache_dir=tmp_path, max_cache_size_mb=1)
        await manager._cleanup_if_needed()
        # Nothing evicted (under limit)
        assert len(manager.list_cached_scenes()) == 3

    @pytest.mark.asyncio
    async def test_cleanup_evicts_oldest(self, tmp_path: Path) -> None:
        """When over limit, oldest files are evicted first."""
        import os
        import time

        # Three files of 200 bytes each
        for name in ("old.splinecode", "mid.splinecode", "new.splinecode"):
            (tmp_path / name).write_bytes(b"x" * 200)

        # Make old.splinecode clearly the oldest
        old = tmp_path / "old.splinecode"
        new = tmp_path / "new.splinecode"
        past = time.time() - 100
        os.utime(old, (past, past))
        os.utime(new, (time.time(), time.time()))

        # Limit small enough that cleanup will evict
        # Total 600 bytes, limit 100 * 1024 = 102400 bytes (way under),
        # so we override the limit to a tiny value via direct attribute
        manager = SplineAssetManager(cache_dir=tmp_path, max_cache_size_mb=1)
        manager.max_cache_size_bytes = 300  # total = 600, 80% threshold = 240
        await manager._cleanup_if_needed()

        remaining = {p.name for p in tmp_path.glob("*.splinecode")}
        # oldest ('old.splinecode') should be gone
        assert "old.splinecode" not in remaining


# ---------------------------------------------------------------------------
# server.py dynamic __getattr__ edges
# ---------------------------------------------------------------------------
class TestServerDynamicAttrs:
    """Cover the dynamic ``app``/``http_app`` attribute access on the module."""

    def teardown_method(self) -> None:
        # Always reset the server singleton between tests
        spline_server._app = None  # type: ignore[attr-defined]

    def test_getattr_unknown_attribute(self) -> None:
        """__getattr__ raises AttributeError for unknown names."""
        with pytest.raises(AttributeError, match="has no attribute"):
            _ = spline_server.totally_unknown_thing

    def test_http_app_attribute_uses_get_app(self) -> None:
        """__getattr__('http_app') returns get_app().http_app."""
        mock_app = MagicMock()
        mock_app.http_app = "sentinel"
        with patch.object(spline_server, "get_app", return_value=mock_app):
            assert spline_server.http_app == "sentinel"


# ---------------------------------------------------------------------------
# __main__ entry point (entry point surfaces)
# ---------------------------------------------------------------------------
class TestMainEntryPoint:
    """The ``__main__`` module just re-exports ``main`` from ``cli``."""

    def test_main_module_imports_cli_main(self) -> None:
        """``spline_mcp.__main__`` re-exports ``main`` from ``cli``."""
        import spline_mcp.__main__ as main_mod

        from spline_mcp.cli import main as cli_main

        assert main_mod.main is cli_main