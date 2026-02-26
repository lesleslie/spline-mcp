"""Integration MCP tools for WebSocket and n8n."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from spline_mcp.config import get_logger_instance, get_settings
from spline_mcp.integrations.n8n import N8NClient, N8NWorkflow
from spline_mcp.integrations.websocket import WebSocketClient, WebSocketStatus

logger = get_logger_instance("spline-mcp.tools.integration")

# Global instances (lazy initialized)
_websocket_client: WebSocketClient | None = None
_n8n_client: N8NClient | None = None


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


async def get_n8n_client() -> N8NClient:
    """Get or create n8n client."""
    global _n8n_client

    if _n8n_client is None:
        settings = get_settings()
        _n8n_client = N8NClient(
            base_url=settings.n8n_url,
            api_key=settings.n8n_api_key,
        )

    return _n8n_client


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

        return {
            "enabled": True,
            **client.get_status_dict(),
        }

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
    async def get_n8n_status() -> dict[str, Any]:
        """Get n8n integration status.

        Returns:
            n8n status and availability
        """
        settings = get_settings()

        if not settings.n8n_enabled:
            return {
                "enabled": False,
                "message": "n8n integration is disabled",
            }

        client = await get_n8n_client()
        available = await client.check_availability()

        return {
            "enabled": True,
            "available": available,
            **client.get_status_dict(),
        }

    @app.tool()
    async def generate_n8n_workflow(
        scene_url: str,
        variable_mappings: dict[str, str],
    ) -> dict[str, Any]:
        """Generate an n8n workflow for Spline variable updates.

        Args:
            scene_url: Spline scene URL
            variable_mappings: Variable name to source mappings

        Returns:
            Generated workflow definition
        """
        settings = get_settings()

        if not settings.n8n_enabled:
            return {
                "success": False,
                "error": "n8n integration is disabled",
            }

        client = await get_n8n_client()

        # Generate workflow
        workflow = client.generate_spline_workflow(scene_url, variable_mappings)

        logger.info(
            "Generated n8n workflow",
            scene_url=scene_url,
            variable_count=len(variable_mappings),
        )

        return {
            "success": True,
            "workflow": workflow.model_dump(),
            "webhook_url": f"{settings.n8n_url}/webhook/spline-update",
            "instructions": {
                "1": "Copy the workflow definition",
                "2": "Import into n8n (Settings > Import from JSON)",
                "3": "Activate the workflow",
                "4": "Use the webhook URL to send updates",
            },
        }

    @app.tool()
    async def trigger_n8n_webhook(
        webhook_path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Trigger an n8n webhook to update scene variables.

        Args:
            webhook_path: Webhook path (e.g., "spline-update")
            payload: Data to send

        Returns:
            Webhook trigger result
        """
        settings = get_settings()

        if not settings.n8n_enabled:
            return {
                "success": False,
                "error": "n8n integration is disabled",
            }

        client = await get_n8n_client()
        result = await client.trigger_webhook(webhook_path, payload)

        if result is None:
            return {
                "success": False,
                "error": "n8n not available or webhook failed",
            }

        logger.info(
            "Triggered n8n webhook",
            webhook_path=webhook_path,
        )

        return {
            "success": True,
            "webhook_path": webhook_path,
            "result": result,
        }

    @app.tool()
    async def get_integration_status() -> dict[str, Any]:
        """Get status of all integrations.

        Returns:
            Status of WebSocket and n8n integrations
        """
        settings = get_settings()

        result = {
            "websocket": {
                "enabled": settings.websocket_enabled,
                "url": settings.websocket_url,
            },
            "n8n": {
                "enabled": settings.n8n_enabled,
                "url": settings.n8n_url,
            },
        }

        if settings.websocket_enabled:
            ws_client = await get_websocket_client()
            result["websocket"]["status"] = ws_client.status.value
            result["websocket"]["connected"] = ws_client.is_connected

        if settings.n8n_enabled:
            n8n_client = await get_n8n_client()
            available = await n8n_client.check_availability()
            result["n8n"]["available"] = available

        return result


__all__ = ["register_integration_tools"]
