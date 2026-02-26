"""Integrations with external services (WebSocket, n8n)."""

from __future__ import annotations

from spline_mcp.integrations.websocket import WebSocketClient, WebSocketStatus
from spline_mcp.integrations.n8n import N8NClient, N8NWorkflow

__all__ = [
    "WebSocketClient",
    "WebSocketStatus",
    "N8NClient",
    "N8NWorkflow",
]
