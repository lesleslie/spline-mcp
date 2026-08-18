"""Tool profile registration groups for spline-mcp MCP server.

Maps ``ToolProfile`` levels to specific ``register_<group>_tools()`` call
lists, controlling which tools are exposed at startup based on the
``SPLINE_TOOL_PROFILE`` environment variable.

Profile tiers:
    MINIMAL:  No tool groups registered (only ``discover_tools`` meta-tool
              + /healthz HTTP route).
    STANDARD: Daily-driver tools — assets (scene CRUD), generation (code
              import/export), helpers (URL utilities), docs (API reference).
              19 tools across 4 groups.
    FULL:     All groups including integration (WebSocket + n8n workflows).
              25 tools across 5 groups.

The dispatch surface (``PROFILE_REGISTRATIONS`` + ``REGISTRATION_MAP`` +
``register_all_tool_groups`` + ``apply_spline_tool_profile``) is consumed
by ``spline_mcp.server.create_app`` which delegates to
``mcp_common.tools.dispatch._apply_tool_profile``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_common.tools import ToolProfile
from mcp_common.tools.dispatch import ALL_TOOLS

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastmcp import FastMCP

MINIMAL_REGISTRATIONS: list[str | Callable[[FastMCP], Awaitable[None] | None]] = []

STANDARD_REGISTRATIONS: list[str | Callable[[FastMCP], Awaitable[None] | None]] = [
    "asset_tools",
    "generation_tools",
    "helper_tools",
    "docs_tools",
]

FULL_REGISTRATIONS: list[str | Callable[[FastMCP], Awaitable[None] | None]] = [
    *STANDARD_REGISTRATIONS,
    "integration_tools",
]

PROFILE_REGISTRATIONS: dict[
    ToolProfile,
    list[str | Callable[[FastMCP], Awaitable[None] | None]] | type[ALL_TOOLS],
] = {
    ToolProfile.MINIMAL: MINIMAL_REGISTRATIONS,
    ToolProfile.STANDARD: STANDARD_REGISTRATIONS,
    ToolProfile.FULL: FULL_REGISTRATIONS,
}


# ---------------------------------------------------------------------------
# W0 apply_tool_profile dispatch surface.
#
# REGISTRATION_MAP routes each group key from PROFILE_REGISTRATIONS to a
# per-group registration callable (taking the FastMCP app). Lazy import keeps
# this module importable without forcing spline_mcp.server to fully evaluate
# the 5 register_*() functions at module import time.
# ---------------------------------------------------------------------------
def _build_registration_map() -> dict[str, Callable[[FastMCP], Awaitable[None] | None]]:
    """Build the {group_key: register_fn(app)} map.

    Local import keeps ``spline_mcp.tools.profiles`` importable without
    forcing every register_X_tools function in ``spline_mcp.tools.*`` to be
    resolved at module import time. Called by
    ``apply_spline_tool_profile`` (not eagerly at import) because server.py
    imports this one at module load.
    """
    from spline_mcp.tools.assets import register_asset_tools
    from spline_mcp.tools.docs import register_docs_tools
    from spline_mcp.tools.generation import register_generation_tools
    from spline_mcp.tools.helpers import register_helper_tools
    from spline_mcp.tools.integration import register_integration_tools

    return {
        "asset_tools": register_asset_tools,
        "generation_tools": register_generation_tools,
        "helper_tools": register_helper_tools,
        "docs_tools": register_docs_tools,
        "integration_tools": register_integration_tools,
    }


def register_all_tool_groups(server: FastMCP) -> None:
    """Bulk register every spline-mcp tool group (called at FULL profile).

    Used as ``register_all_fn`` for the W0 helper. Imports each
    register_<group>_tools directly (not via REGISTRATION_MAP iteration) so
    that adding a new group requires editing both this function and the
    FULL_REGISTRATIONS list — the redundancy is intentional: each is the
    ground-truth for a separate concern.
    """
    from spline_mcp.tools.assets import register_asset_tools
    from spline_mcp.tools.docs import register_docs_tools
    from spline_mcp.tools.generation import register_generation_tools
    from spline_mcp.tools.helpers import register_helper_tools
    from spline_mcp.tools.integration import register_integration_tools

    register_generation_tools(server)
    register_asset_tools(server)
    register_helper_tools(server)
    register_integration_tools(server)
    register_docs_tools(server)


async def apply_spline_tool_profile(server: FastMCP) -> None:
    """Apply the SPLINE_TOOL_PROFILE dispatch to ``server`` at startup.

    Async because the W0 helper is async; called from
    ``spline_mcp.server.create_app`` via the sync ``apply_tool_profile``
    wrapper at module import time (no event loop running).
    """
    from mcp_common.tools.dispatch import _apply_tool_profile

    await _apply_tool_profile(
        server,
        profile_env_var="SPLINE_TOOL_PROFILE",
        registrations=PROFILE_REGISTRATIONS,
        registration_map=_build_registration_map(),
        register_all_fn=register_all_tool_groups,
        mandatory_groups=set(),
        essential_tool_names=set(),
    )


__all__ = [
    "FULL_REGISTRATIONS",
    "MINIMAL_REGISTRATIONS",
    "PROFILE_REGISTRATIONS",
    "STANDARD_REGISTRATIONS",
    "_build_registration_map",
    "apply_spline_tool_profile",
    "register_all_tool_groups",
]
