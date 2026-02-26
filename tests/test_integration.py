"""Integration tests for WebSocket and n8n integrations."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from spline_mcp.integrations.websocket import (
    WebSocketClient,
    WebSocketMessage,
    WebSocketStatus,
)
from spline_mcp.integrations.n8n import N8NClient, N8NWorkflow


class TestWebSocketClient:
    """Tests for WebSocket client."""

    def test_initialization(self) -> None:
        """Test client initialization."""
        client = WebSocketClient(
            url="ws://localhost:8690",
            auto_reconnect=True,
            reconnect_delay=5.0,
            max_reconnect_attempts=3,
        )

        assert client.url == "ws://localhost:8690"
        assert client.auto_reconnect is True
        assert client.reconnect_delay == 5.0
        assert client.max_reconnect_attempts == 3
        assert client.status == WebSocketStatus.DISCONNECTED
        assert not client.is_connected

    @pytest.mark.asyncio
    async def test_soft_failover_on_connection_failure(self) -> None:
        """Test that connection failure doesn't raise exception."""
        client = WebSocketClient(
            url="ws://localhost:99999",  # Invalid port
            auto_reconnect=False,
        )

        # Should return False, not raise
        result = await client.connect()
        assert result is False
        assert client.status == WebSocketStatus.ERROR

    @pytest.mark.asyncio
    async def test_subscribe_without_connection(self) -> None:
        """Test subscribing when not connected."""
        client = WebSocketClient(url="ws://localhost:8690")

        handler = MagicMock()
        unsubscribe = await client.subscribe("test-channel", handler)

        # Should still register subscriber
        assert "test-channel" in client._subscribers
        assert handler in client._subscribers["test-channel"]

    def test_status_dict(self) -> None:
        """Test status dictionary output."""
        client = WebSocketClient(url="ws://localhost:8690")
        status = client.get_status_dict()

        assert "url" in status
        assert "status" in status
        assert "is_connected" in status
        assert status["url"] == "ws://localhost:8690"
        assert status["status"] == WebSocketStatus.DISCONNECTED.value

    @pytest.mark.asyncio
    async def test_message_handler_setup(self) -> None:
        """Test message handler is set up correctly."""
        client = WebSocketClient(url="ws://localhost:8690")

        received_messages: list[dict] = []

        def handler(data: dict) -> None:
            received_messages.append(data)

        await client.subscribe("test-channel", handler)

        # Verify handler is registered
        assert "test-channel" in client._subscribers

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """Test disconnect cleans up properly."""
        client = WebSocketClient(url="ws://localhost:8690")
        await client.disconnect()

        assert client.status == WebSocketStatus.DISCONNECTED
        assert client._websocket is None
        assert client._task is None


class TestWebSocketMessage:
    """Tests for WebSocket message model."""

    def test_message_creation(self) -> None:
        """Test message creation."""
        msg = WebSocketMessage(
            type="publish",
            channel="spline:variables",
            payload={"color": "#ff0000"},
        )

        assert msg.type == "publish"
        assert msg.channel == "spline:variables"
        assert msg.payload == {"color": "#ff0000"}

    def test_message_serialization(self) -> None:
        """Test message JSON serialization."""
        msg = WebSocketMessage(
            type="subscribe",
            channel="test",
        )

        json_str = msg.model_dump_json()
        assert '"type":"subscribe"' in json_str
        assert '"channel":"test"' in json_str


class TestN8NClient:
    """Tests for n8n client."""

    def test_initialization(self) -> None:
        """Test client initialization."""
        client = N8NClient(
            base_url="http://localhost:3044",
            api_key="test-key",
        )

        assert client.base_url == "http://localhost:3044"
        assert client.api_key == "test-key"
        assert client._available is None  # Not checked yet

    @pytest.mark.asyncio
    async def test_soft_failover_on_unavailable(self) -> None:
        """Test that unavailable n8n doesn't raise exception."""
        client = N8NClient(base_url="http://localhost:99999")

        available = await client.check_availability()
        assert available is False
        assert client._available is False

    @pytest.mark.asyncio
    async def test_create_workflow_unavailable(self) -> None:
        """Test workflow creation when n8n unavailable."""
        client = N8NClient(base_url="http://localhost:99999")

        workflow = N8NWorkflow(name="Test")
        result = await client.create_workflow(workflow)

        # Should return None gracefully
        assert result is None

    @pytest.mark.asyncio
    async def test_trigger_webhook_unavailable(self) -> None:
        """Test webhook trigger when n8n unavailable."""
        client = N8NClient(base_url="http://localhost:99999")

        result = await client.trigger_webhook("test", {"data": "value"})

        # Should return None gracefully
        assert result is None

    def test_generate_spline_workflow(self) -> None:
        """Test Spline workflow generation."""
        client = N8NClient(base_url="http://localhost:3044")

        workflow = client.generate_spline_workflow(
            scene_url="https://prod.spline.design/test/scene.splinecode",
            variable_mappings={
                "color": "data.color",
                "speed": "data.speed",
            },
        )

        assert workflow.name.startswith("Spline Update")
        assert len(workflow.nodes) == 3
        assert workflow.nodes[0]["type"] == "n8n-nodes-base.webhook"

    def test_status_dict(self) -> None:
        """Test status dictionary output."""
        client = N8NClient(
            base_url="http://localhost:3044",
            api_key="secret",
        )
        status = client.get_status_dict()

        assert "base_url" in status
        assert "available" in status
        assert "has_api_key" in status
        assert status["base_url"] == "http://localhost:3044"
        assert status["has_api_key"] is True


class TestN8NWorkflow:
    """Tests for n8n workflow model."""

    def test_workflow_creation(self) -> None:
        """Test workflow creation."""
        workflow = N8NWorkflow(
            name="Test Workflow",
            nodes=[
                {"type": "n8n-nodes-base.webhook", "name": "Webhook"},
            ],
            connections={},
        )

        assert workflow.name == "Test Workflow"
        assert len(workflow.nodes) == 1
        assert workflow.nodes[0]["type"] == "n8n-nodes-base.webhook"


class TestIntegrationScenarios:
    """Tests for integration scenarios."""

    @pytest.mark.asyncio
    async def test_websocket_reconnect_scenario(self) -> None:
        """Test WebSocket reconnection behavior."""
        client = WebSocketClient(
            url="ws://localhost:8690",
            auto_reconnect=True,
            max_reconnect_attempts=2,
            reconnect_delay=0.1,
        )

        # Attempt connection (will fail without server)
        await client.connect()

        # Should have attempted but failed
        assert client.status in [WebSocketStatus.ERROR, WebSocketStatus.DISCONNECTED]

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self) -> None:
        """Test multiple subscribers on same channel."""
        client = WebSocketClient(url="ws://localhost:8690")

        handler1 = MagicMock()
        handler2 = MagicMock()
        handler3 = MagicMock()

        await client.subscribe("test-channel", handler1)
        await client.subscribe("test-channel", handler2)
        await client.subscribe("other-channel", handler3)

        assert len(client._subscribers["test-channel"]) == 2
        assert len(client._subscribers["other-channel"]) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self) -> None:
        """Test unsubscribe functionality."""
        client = WebSocketClient(url="ws://localhost:8690")

        handler = MagicMock()
        unsubscribe = await client.subscribe("test-channel", handler)

        assert "test-channel" in client._subscribers

        # Unsubscribe
        unsubscribe()

        assert handler not in client._subscribers.get("test-channel", [])


class TestSoftFailover:
    """Tests for soft failover behavior."""

    @pytest.mark.asyncio
    async def test_websocket_unavailable_continue(self) -> None:
        """Test that WebSocket unavailability doesn't break operation."""
        client = WebSocketClient(
            url="ws://nonexistent:9999",
            auto_reconnect=False,
        )

        # Connection should fail gracefully
        connected = await client.connect()
        assert connected is False

        # Client should still be usable
        assert client.status == WebSocketStatus.ERROR
        assert not client.is_connected

        # Operations should not raise
        status = client.get_status_dict()
        assert status["status"] == WebSocketStatus.ERROR.value

    @pytest.mark.asyncio
    async def test_n8n_unavailable_continue(self) -> None:
        """Test that n8n unavailability doesn't break operation."""
        client = N8NClient(base_url="http://nonexistent:9999")

        # Check should fail gracefully
        available = await client.check_availability()
        assert available is False

        # Operations should return None, not raise
        result = await client.create_workflow(N8NWorkflow(name="Test"))
        assert result is None

        result = await client.trigger_webhook("test", {})
        assert result is None

    @pytest.mark.asyncio
    async def test_both_integrations_unavailable(self) -> None:
        """Test operation when both integrations unavailable."""
        ws_client = WebSocketClient(url="ws://nonexistent:9999")
        n8n_client = N8NClient(base_url="http://nonexistent:9999")

        # Both should fail gracefully
        ws_connected = await ws_client.connect()
        n8n_available = await n8n_client.check_availability()

        assert ws_connected is False
        assert n8n_available is False

        # Code generation should still work
        from spline_mcp.generators.react import ReactGenerator

        generator = ReactGenerator()
        code = generator.generate_component(
            "https://prod.spline.design/test/scene.splinecode"
        )

        assert "Spline" in code
        assert code is not None


class TestConfiguration:
    """Tests for configuration integration."""

    def test_websocket_config_from_settings(self) -> None:
        """Test WebSocket client from settings."""
        from spline_mcp.config import get_settings

        settings = get_settings()
        client = WebSocketClient(
            url=settings.websocket_url,
            auto_reconnect=settings.websocket_auto_reconnect,
        )

        assert client.url == settings.websocket_url
        assert client.auto_reconnect == settings.websocket_auto_reconnect

    def test_n8n_config_from_settings(self) -> None:
        """Test n8n client from settings."""
        from spline_mcp.config import get_settings

        settings = get_settings()
        client = N8NClient(
            base_url=settings.n8n_url,
            api_key=settings.n8n_api_key,
        )

        assert client.base_url == settings.n8n_url
