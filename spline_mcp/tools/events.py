"""Event management tools for Spline MCP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from spline_mcp.config import get_logger_instance, get_settings

if TYPE_CHECKING:
    pass

logger = get_logger_instance("spline-mcp.tools.events")


def register_event_tools(app: FastMCP) -> None:
    """Register event and action management tools."""

    @app.tool()
    async def list_events(scene_id: str) -> list[dict[str, Any]]:
        """List all events in a Spline scene.

        Args:
            scene_id: The unique identifier of the scene

        Returns:
            List of event dictionaries
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            events = await client.list_events(scene_id)
            logger.info("Listed events", scene_id=scene_id, count=len(events))
            return [evt.model_dump() for evt in events]

    @app.tool()
    async def create_event(
        scene_id: str,
        name: str,
        event_type: str,
        target_object_id: str | None = None,
        actions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new event in a scene.

        Args:
            scene_id: The unique identifier of the scene
            name: Name for the new event
            event_type: Type of event (click, hover, mouse_down, mouse_up, load, etc.)
            target_object_id: Optional target object that triggers the event
            actions: List of actions to execute when event fires

        Returns:
            Created event details
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            event = await client.create_event(
                scene_id=scene_id,
                name=name,
                event_type=event_type,
                target_object_id=target_object_id,
                actions=actions,
            )
            logger.info(
                "Created event",
                scene_id=scene_id,
                event_id=event.id,
                name=name,
                type=event_type,
            )
            return event.model_dump()

    @app.tool()
    async def trigger_event(scene_id: str, event_id: str) -> dict[str, Any]:
        """Manually trigger an event.

        Args:
            scene_id: The unique identifier of the scene
            event_id: The unique identifier of the event to trigger

        Returns:
            Result of the event execution
        """
        from spline_mcp.client import SplineClient

        settings = get_settings()
        if not settings.api_key:
            raise ValueError("SPLINE_API_KEY not configured")

        async with SplineClient(settings.api_key, settings.api_base_url) as client:
            result = await client.trigger_event(scene_id, event_id)
            logger.info(
                "Triggered event",
                scene_id=scene_id,
                event_id=event_id,
            )
            return result
