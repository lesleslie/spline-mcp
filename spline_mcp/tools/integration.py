"""Integration MCP tools for WebSocket."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from spline_mcp.config import get_logger_instance, get_settings
from spline_mcp.integrations.websocket import WebSocketClient

logger = get_logger_instance("spline-mcp.tools.integration")

# Global instances (lazy initialized)
_websocket_client: WebSocketClient | None = None


async def get_websocket_client() -> WebSocketClient:
    """Get or create WebSocket client."""
    global _websocket_client

    if _websocket_client is None:
        settings = get_settings()
        _websocket_client = WebSocketClient(
            url=settings.websocket_url,
            auto_reconnect=settings.websocket_auto_reconnect,
        )

        if settings.websocket_enabled:
            await _websocket_client.connect()

    return _websocket_client


def register_integration_tools(app: FastMCP) -> None:
    """Register integration tools."""

    @app.tool()
    async def get_websocket_status() -> dict[str, Any]:
        """Get WebSocket connection status.

        Returns:
            WebSocket status and configuration
        """
        settings = get_settings()

        if not settings.websocket_enabled:
            return {
                "enabled": False,
                "message": "WebSocket integration is disabled",
            }

        client = await get_websocket_client()

        return {"enabled": True} | client.get_status_dict()

    @app.tool()
    async def subscribe_to_channel(
        channel: str,
    ) -> dict[str, Any]:
        """Subscribe to a WebSocket channel for real-time updates.

        Args:
            channel: Channel name to subscribe to

        Returns:
            Subscription status
        """
        settings = get_settings()

        if not settings.websocket_enabled:
            return {
                "success": False,
                "error": "WebSocket integration is disabled",
            }

        client = await get_websocket_client()

        if not client.is_connected:
            return {
                "success": False,
                "error": "WebSocket not connected",
                "status": client.status.value,
            }

        # Subscribe (note: actual message handling would need client code)
        await client.subscribe(channel, lambda data: None)

        logger.info("Subscribed to channel", channel=channel)

        return {
            "success": True,
            "channel": channel,
            "message": f"Subscribed to {channel}. Generated code will receive updates.",
        }

    @app.tool()
    async def get_integration_status() -> dict[str, Any]:
        """Get status of integrations.

        Returns:
            Status of WebSocket integration
        """
        settings = get_settings()

        result = {
            "websocket": {
                "enabled": settings.websocket_enabled,
                "url": settings.websocket_url,
            },
        }

        if settings.websocket_enabled:
            ws_client = await get_websocket_client()
            result["websocket"]["status"] = ws_client.status.value
            result["websocket"]["connected"] = ws_client.is_connected

        return result


__all__ = ["register_integration_tools"]
