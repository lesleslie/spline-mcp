"""n8n integration with soft failover."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field

from spline_mcp.config import get_logger_instance

logger = get_logger_instance("spline-mcp.n8n")


class N8NWorkflow(BaseModel):
    """n8n workflow definition for Spline integration."""

    name: str = Field(..., description="Workflow name")
    nodes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Workflow nodes",
    )
    connections: dict[str, Any] = Field(
        default_factory=dict,
        description="Node connections",
    )
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow settings",
    )


class N8NClient:
    """n8n client with soft failover.

    Provides integration with n8n for workflow automation.
    Gracefully handles unavailability.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3044",
        api_key: str | None = None,
    ) -> None:
        """Initialize n8n client.

        Args:
            base_url: n8n server URL
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None
        self._available: bool | None = None

        logger.info(
            "n8n client initialized",
            base_url=base_url,
            has_api_key=bool(api_key),
        )

    async def __aenter__(self) -> "N8NClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers

    async def check_availability(self) -> bool:
        """Check if n8n server is available.

        Returns:
            True if available, False otherwise
        """
        if self._available is not None:
            return self._available

        try:
            client = self._get_client()
            response = await client.get(
                f"{self.base_url}/healthz",
                headers=self._get_headers(),
                timeout=5.0,
            )
            self._available = response.is_success

            if self._available:
                logger.info("n8n server is available")
            else:
                logger.warning(
                    "n8n server returned error status",
                    status_code=response.status_code,
                )

        except Exception as e:
            self._available = False
            logger.warning(
                "n8n server not available, workflow features disabled",
                error=str(e),
            )

        return self._available

    async def create_workflow(
        self,
        workflow: N8NWorkflow,
    ) -> dict[str, Any] | None:
        """Create an n8n workflow.

        Args:
            workflow: Workflow definition

        Returns:
            Created workflow data or None if unavailable
        """
        if not await self.check_availability():
            logger.warning(
                "Cannot create workflow, n8n not available",
                workflow_name=workflow.name,
            )
            return None

        try:
            client = self._get_client()
            response = await client.post(
                f"{self.base_url}/api/v1/workflows",
                headers=self._get_headers(),
                json={
                    "name": workflow.name,
                    "nodes": workflow.nodes,
                    "connections": workflow.connections,
                    "settings": workflow.settings,
                },
            )
            response.raise_for_status()

            logger.info(
                "Created n8n workflow",
                workflow_name=workflow.name,
            )

            return response.json()

        except Exception as e:
            logger.warning(
                "Failed to create n8n workflow",
                workflow_name=workflow.name,
                error=str(e),
            )
            return None

    async def trigger_webhook(
        self,
        webhook_path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Trigger an n8n webhook.

        Args:
            webhook_path: Webhook path (e.g., "spline-update")
            payload: Data to send

        Returns:
            Response data or None if unavailable
        """
        if not await self.check_availability():
            logger.debug(
                "Cannot trigger webhook, n8n not available",
                webhook_path=webhook_path,
            )
            return None

        try:
            client = self._get_client()
            response = await client.post(
                f"{self.base_url}/webhook/{webhook_path}",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()

            logger.debug(
                "Triggered n8n webhook",
                webhook_path=webhook_path,
            )

            return response.json()

        except Exception as e:
            logger.warning(
                "Failed to trigger n8n webhook",
                webhook_path=webhook_path,
                error=str(e),
            )
            return None

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def generate_spline_workflow(
        self,
        scene_url: str,
        variable_mappings: dict[str, str],
    ) -> N8NWorkflow:
        """Generate an n8n workflow for Spline variable updates.

        Args:
            scene_url: Spline scene URL
            variable_mappings: Variable name to source mappings

        Returns:
            N8NWorkflow definition
        """
        # Webhook trigger node
        webhook_node = {
            "parameters": {
                "httpMethod": "POST",
                "path": "spline-update",
                "responseMode": "onReceived",
            },
            "name": "Webhook Trigger",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [250, 300],
        }

        # Set variables node
        set_variables = {
            "parameters": {
                "values": {
                    "string": [
                        {"name": "scene_url", "value": scene_url},
                    ],
                },
            },
            "name": "Set Variables",
            "type": "n8n-nodes-base.set",
            "typeVersion": 2,
            "position": [450, 300],
        }

        # Add variable mappings
        for i, (var_name, source) in enumerate(variable_mappings.items()):
            set_variables["parameters"]["values"]["string"].append({
                "name": var_name,
                "value": f"={{ $json.{source} }}",
            })

        # HTTP request node (for client notification)
        http_node = {
            "parameters": {
                "url": "={{ $json.callback_url }}",
                "method": "POST",
                "jsonParameters": True,
                "bodyParametersJson": "={{ $json }}",
            },
            "name": "Notify Client",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [650, 300],
        }

        return N8NWorkflow(
            name=f"Spline Update - {scene_url.split('/')[-2]}",
            nodes=[webhook_node, set_variables, http_node],
            connections={
                "Webhook Trigger": {
                    "main": [[{"node": "Set Variables", "type": "main", "index": 0}]],
                },
                "Set Variables": {
                    "main": [[{"node": "Notify Client", "type": "main", "index": 0}]],
                },
            },
            settings={},
        )

    def get_status_dict(self) -> dict[str, Any]:
        """Get status as dictionary."""
        return {
            "base_url": self.base_url,
            "available": self._available,
            "has_api_key": bool(self.api_key),
        }


__all__ = ["N8NClient", "N8NWorkflow"]
