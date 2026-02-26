"""WebSocket integration with soft failover for Mahavishnu."""

from __future__ import annotations

import asyncio
import json
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field

from spline_mcp.config import get_logger_instance

logger = get_logger_instance("spline-mcp.websocket")


class WebSocketStatus(str, Enum):
    """WebSocket connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""

    type: str = Field(..., description="Message type")
    channel: str | None = Field(default=None, description="Target channel")
    payload: Any = Field(default=None, description="Message payload")


class WebSocketClient:
    """WebSocket client with soft failover for Mahavishnu integration.

    This client gracefully handles connection failures and continues
    operation without WebSocket support when unavailable.
    """

    def __init__(
        self,
        url: str = "ws://localhost:8690",
        auto_reconnect: bool = True,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 3,
    ) -> None:
        """Initialize WebSocket client with soft failover.

        Args:
            url: WebSocket server URL
            auto_reconnect: Whether to attempt reconnection on disconnect
            reconnect_delay: Delay between reconnection attempts in seconds
            max_reconnect_attempts: Maximum reconnection attempts
        """
        self.url = url
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        self._status = WebSocketStatus.DISCONNECTED
        self._subscribers: dict[str, list[Callable[[Any], None]]] = {}
        self._reconnect_count = 0
        self._websocket: Any = None  # websockets.WebSocketClientProtocol
        self._task: asyncio.Task | None = None

        logger.info(
            "WebSocket client initialized",
            url=url,
            auto_reconnect=auto_reconnect,
        )

    @property
    def status(self) -> WebSocketStatus:
        """Get current connection status."""
        return self._status

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._status == WebSocketStatus.CONNECTED

    async def connect(self) -> bool:
        """Connect to WebSocket server with soft failover.

        Returns:
            True if connected, False if failed (but doesn't raise)
        """
        if self._status == WebSocketStatus.CONNECTED:
            return True

        self._status = WebSocketStatus.CONNECTING

        try:
            import websockets
        except ImportError:
            logger.warning(
                "websockets library not installed, WebSocket integration disabled",
                hint="pip install websockets",
            )
            self._status = WebSocketStatus.ERROR
            return False

        try:
            self._websocket = await asyncio.wait_for(
                websockets.connect(self.url),
                timeout=10.0,
            )
            self._status = WebSocketStatus.CONNECTED
            self._reconnect_count = 0

            logger.info(
                "WebSocket connected to Mahavishnu",
                url=self.url,
            )

            # Start message handler
            self._task = asyncio.create_task(self._message_handler())

            return True

        except asyncio.TimeoutError:
            logger.warning(
                "WebSocket connection timeout, continuing without real-time updates",
                url=self.url,
            )
            self._status = WebSocketStatus.ERROR
            return False

        except Exception as e:
            logger.warning(
                "WebSocket connection failed, continuing without real-time updates",
                url=self.url,
                error=str(e),
            )
            self._status = WebSocketStatus.ERROR
            return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None

        self._status = WebSocketStatus.DISCONNECTED
        logger.info("WebSocket disconnected")

    async def subscribe(
        self,
        channel: str,
        handler: Callable[[Any], None],
    ) -> Callable[[], None]:
        """Subscribe to a channel with message handler.

        Args:
            channel: Channel name to subscribe to
            handler: Callback function for messages

        Returns:
            Unsubscribe function
        """
        if channel not in self._subscribers:
            self._subscribers[channel] = []

        self._subscribers[channel].append(handler)

        # Send subscription message if connected
        if self.is_connected:
            await self._send(WebSocketMessage(
                type="subscribe",
                channel=channel,
            ))

        logger.debug("Subscribed to channel", channel=channel)

        def unsubscribe() -> None:
            if channel in self._subscribers:
                try:
                    self._subscribers[channel].remove(handler)
                except ValueError:
                    pass

        return unsubscribe

    async def publish(
        self,
        channel: str,
        payload: Any,
    ) -> bool:
        """Publish a message to a channel.

        Args:
            channel: Target channel
            payload: Message payload

        Returns:
            True if sent, False if not connected
        """
        if not self.is_connected:
            logger.debug(
                "Cannot publish, WebSocket not connected",
                channel=channel,
            )
            return False

        await self._send(WebSocketMessage(
            type="publish",
            channel=channel,
            payload=payload,
        ))

        return True

    async def _send(self, message: WebSocketMessage) -> None:
        """Send a message over WebSocket."""
        if not self._websocket:
            return

        try:
            await self._websocket.send(message.model_dump_json())
        except Exception as e:
            logger.warning(
                "Failed to send WebSocket message",
                error=str(e),
            )

    async def _message_handler(self) -> None:
        """Handle incoming WebSocket messages."""
        if not self._websocket:
            return

        try:
            async for raw_message in self._websocket:
                try:
                    data = json.loads(raw_message)
                    message = WebSocketMessage(**data)

                    # Dispatch to subscribers
                    if message.channel and message.channel in self._subscribers:
                        for handler in self._subscribers[message.channel]:
                            try:
                                handler(message.payload)
                            except Exception as e:
                                logger.warning(
                                    "Error in message handler",
                                    channel=message.channel,
                                    error=str(e),
                                )

                except json.JSONDecodeError:
                    logger.warning("Invalid JSON message received")

        except Exception as e:
            logger.warning(
                "WebSocket connection lost",
                error=str(e),
            )
            self._status = WebSocketStatus.ERROR

            # Attempt reconnection if enabled
            if self.auto_reconnect and self._reconnect_count < self.max_reconnect_attempts:
                self._reconnect_count += 1
                logger.info(
                    "Attempting reconnection",
                    attempt=self._reconnect_count,
                    max_attempts=self.max_reconnect_attempts,
                )

                await asyncio.sleep(self.reconnect_delay)
                await self.connect()

    def get_status_dict(self) -> dict[str, Any]:
        """Get status as dictionary."""
        return {
            "url": self.url,
            "status": self._status.value,
            "is_connected": self.is_connected,
            "subscribers": {
                channel: len(handlers)
                for channel, handlers in self._subscribers.items()
            },
        }


__all__ = ["WebSocketClient", "WebSocketStatus", "WebSocketMessage"]
