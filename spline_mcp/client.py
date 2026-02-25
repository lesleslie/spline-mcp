"""Spline API client for 3D scene operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class SplineObject(BaseModel):
    """3D object in a Spline scene."""

    id: str = Field(..., description="Unique object identifier")
    name: str = Field(..., description="Object name")
    type: str = Field(..., description="Object type (mesh, light, camera, etc.)")
    position: list[float] = Field(default=[0, 0, 0], description="XYZ position")
    rotation: list[float] = Field(default=[0, 0, 0], description="XYZ rotation in degrees")
    scale: list[float] = Field(default=[1, 1, 1], description="XYZ scale")
    visible: bool = Field(default=True, description="Object visibility")
    locked: bool = Field(default=False, description="Object lock state")
    properties: dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class SplineMaterial(BaseModel):
    """Material definition for 3D objects."""

    id: str = Field(..., description="Unique material identifier")
    name: str = Field(..., description="Material name")
    color: str = Field(default="#ffffff", description="Base color (hex)")
    metalness: float = Field(default=0.0, ge=0.0, le=1.0, description="Metalness factor")
    roughness: float = Field(default=0.5, ge=0.0, le=1.0, description="Roughness factor")
    opacity: float = Field(default=1.0, ge=0.0, le=1.0, description="Opacity")
    emissive: str | None = Field(default=None, description="Emissive color (hex)")
    properties: dict[str, Any] = Field(default_factory=dict, description="Additional properties")


class SplineEvent(BaseModel):
    """Event definition for scene interactions."""

    id: str = Field(..., description="Unique event identifier")
    name: str = Field(..., description="Event name")
    event_type: str = Field(..., description="Event type (click, hover, load, etc.)")
    target_object_id: str | None = Field(default=None, description="Target object ID")
    actions: list[dict[str, Any]] = Field(default_factory=list, description="Actions to execute")


class SplineScene(BaseModel):
    """Spline scene representation."""

    id: str = Field(..., description="Scene identifier")
    name: str = Field(..., description="Scene name")
    objects: list[SplineObject] = Field(default_factory=list, description="Scene objects")
    materials: list[SplineMaterial] = Field(default_factory=list, description="Scene materials")
    events: list[SplineEvent] = Field(default_factory=list, description="Scene events")
    properties: dict[str, Any] = Field(default_factory=dict, description="Scene properties")


class SplineClient:
    """Async client for Spline API operations."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.spline.design/v1",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Spline API client."""
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "SplineClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    # Scene Operations
    async def list_scenes(self) -> list[dict[str, Any]]:
        """List all accessible scenes."""
        client = self._get_client()
        response = await client.get("/scenes")
        response.raise_for_status()
        return response.json().get("scenes", [])

    async def get_scene(self, scene_id: str) -> SplineScene:
        """Get scene details by ID."""
        client = self._get_client()
        response = await client.get(f"/scenes/{scene_id}")
        response.raise_for_status()
        return SplineScene(**response.json())

    async def create_scene(self, name: str, **properties: Any) -> SplineScene:
        """Create a new scene."""
        client = self._get_client()
        payload = {"name": name, **properties}
        response = await client.post("/scenes", json=payload)
        response.raise_for_status()
        return SplineScene(**response.json())

    async def delete_scene(self, scene_id: str) -> bool:
        """Delete a scene."""
        client = self._get_client()
        response = await client.delete(f"/scenes/{scene_id}")
        response.raise_for_status()
        return response.status_code == 204

    # Object Operations
    async def list_objects(self, scene_id: str) -> list[SplineObject]:
        """List all objects in a scene."""
        client = self._get_client()
        response = await client.get(f"/scenes/{scene_id}/objects")
        response.raise_for_status()
        return [SplineObject(**obj) for obj in response.json().get("objects", [])]

    async def get_object(self, scene_id: str, object_id: str) -> SplineObject:
        """Get object details."""
        client = self._get_client()
        response = await client.get(f"/scenes/{scene_id}/objects/{object_id}")
        response.raise_for_status()
        return SplineObject(**response.json())

    async def create_object(
        self,
        scene_id: str,
        name: str,
        object_type: str,
        position: list[float] | None = None,
        rotation: list[float] | None = None,
        scale: list[float] | None = None,
        **properties: Any,
    ) -> SplineObject:
        """Create a new 3D object."""
        client = self._get_client()
        payload: dict[str, Any] = {
            "name": name,
            "type": object_type,
        }
        if position:
            payload["position"] = position
        if rotation:
            payload["rotation"] = rotation
        if scale:
            payload["scale"] = scale
        payload.update(properties)

        response = await client.post(f"/scenes/{scene_id}/objects", json=payload)
        response.raise_for_status()
        return SplineObject(**response.json())

    async def update_object(
        self,
        scene_id: str,
        object_id: str,
        **updates: Any,
    ) -> SplineObject:
        """Update object properties."""
        client = self._get_client()
        response = await client.patch(
            f"/scenes/{scene_id}/objects/{object_id}",
            json=updates,
        )
        response.raise_for_status()
        return SplineObject(**response.json())

    async def delete_object(self, scene_id: str, object_id: str) -> bool:
        """Delete an object from a scene."""
        client = self._get_client()
        response = await client.delete(f"/scenes/{scene_id}/objects/{object_id}")
        response.raise_for_status()
        return response.status_code == 204

    # Material Operations
    async def list_materials(self, scene_id: str) -> list[SplineMaterial]:
        """List all materials in a scene."""
        client = self._get_client()
        response = await client.get(f"/scenes/{scene_id}/materials")
        response.raise_for_status()
        return [SplineMaterial(**mat) for mat in response.json().get("materials", [])]

    async def create_material(
        self,
        scene_id: str,
        name: str,
        color: str = "#ffffff",
        metalness: float = 0.0,
        roughness: float = 0.5,
        **properties: Any,
    ) -> SplineMaterial:
        """Create a new material."""
        client = self._get_client()
        payload = {
            "name": name,
            "color": color,
            "metalness": metalness,
            "roughness": roughness,
            **properties,
        }
        response = await client.post(f"/scenes/{scene_id}/materials", json=payload)
        response.raise_for_status()
        return SplineMaterial(**response.json())

    async def apply_material(
        self,
        scene_id: str,
        object_id: str,
        material_id: str,
    ) -> SplineObject:
        """Apply a material to an object."""
        client = self._get_client()
        response = await client.post(
            f"/scenes/{scene_id}/objects/{object_id}/material",
            json={"material_id": material_id},
        )
        response.raise_for_status()
        return SplineObject(**response.json())

    # Event Operations
    async def list_events(self, scene_id: str) -> list[SplineEvent]:
        """List all events in a scene."""
        client = self._get_client()
        response = await client.get(f"/scenes/{scene_id}/events")
        response.raise_for_status()
        return [SplineEvent(**evt) for evt in response.json().get("events", [])]

    async def create_event(
        self,
        scene_id: str,
        name: str,
        event_type: str,
        target_object_id: str | None = None,
        actions: list[dict[str, Any]] | None = None,
    ) -> SplineEvent:
        """Create a new event."""
        client = self._get_client()
        payload: dict[str, Any] = {
            "name": name,
            "event_type": event_type,
        }
        if target_object_id:
            payload["target_object_id"] = target_object_id
        if actions:
            payload["actions"] = actions

        response = await client.post(f"/scenes/{scene_id}/events", json=payload)
        response.raise_for_status()
        return SplineEvent(**response.json())

    async def trigger_event(self, scene_id: str, event_id: str) -> dict[str, Any]:
        """Trigger an event."""
        client = self._get_client()
        response = await client.post(f"/scenes/{scene_id}/events/{event_id}/trigger")
        response.raise_for_status()
        return response.json()

    # Runtime API
    async def get_runtime_state(self, scene_id: str) -> dict[str, Any]:
        """Get current runtime state of a scene."""
        client = self._get_client()
        response = await client.get(f"/scenes/{scene_id}/runtime/state")
        response.raise_for_status()
        return response.json()

    async def set_variable(
        self,
        scene_id: str,
        variable_name: str,
        value: Any,
    ) -> dict[str, Any]:
        """Set a runtime variable."""
        client = self._get_client()
        response = await client.post(
            f"/scenes/{scene_id}/runtime/variables",
            json={"name": variable_name, "value": value},
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


__all__ = [
    "SplineClient",
    "SplineObject",
    "SplineMaterial",
    "SplineEvent",
    "SplineScene",
]
