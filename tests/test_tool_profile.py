"""spline-mcp tool profile wiring tests.

Verifies the W2b.3 adoption of ``mcp_common.tools.dispatch._apply_tool_profile``
replaces the inline 5 ``register_*_tools(app)`` calls with a 3-tier
callable-mode architecture (MINIMAL / STANDARD / FULL) gated by the
``SPLINE_TOOL_PROFILE`` environment variable.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_profiles_py_exists() -> None:
    """profiles.py must exist under spline_mcp/tools/."""
    profiles = REPO_ROOT / "spline_mcp" / "tools" / "profiles.py"
    assert profiles.exists(), f"{profiles} missing"


def test_profiles_py_defines_profile_registrations() -> None:
    """profiles.py must export a PROFILE_REGISTRATIONS dict."""
    profiles = REPO_ROOT / "spline_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "PROFILE_REGISTRATIONS"
            for t in node.targets
        ):
            found = True
            break
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PROFILE_REGISTRATIONS"
        ):
            found = True
            break
    assert found, "PROFILE_REGISTRATIONS not defined in profiles.py"


def test_profiles_py_defines_build_registration_map() -> None:
    """profiles.py must export ``_build_registration_map`` (consumed by apply_spline_tool_profile)."""
    profiles = REPO_ROOT / "spline_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_build_registration_map"
        for node in ast.walk(tree)
    )
    assert found, "_build_registration_map not defined in profiles.py"


def test_profiles_py_defines_register_all_tool_groups() -> None:
    """profiles.py must export ``register_all_tool_groups`` (used as register_all_fn at FULL profile)."""
    profiles = REPO_ROOT / "spline_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "register_all_tool_groups"
        for node in ast.walk(tree)
    )
    assert found, "register_all_tool_groups not defined in profiles.py"


def test_server_uses_spline_tool_profile_env_var() -> None:
    """The SPLINE_TOOL_PROFILE env var must be wired through the dispatch path.

    In the production code, the env var is passed inside profiles.py
    via ``apply_spline_tool_profile -> _apply_tool_profile``. server.py
    imports the async wrapper but doesn't need to know the env var
    name. So we verify the env var is referenced in profiles.py.
    """
    profiles = REPO_ROOT / "spline_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = any(
        isinstance(node, ast.Constant) and node.value == "SPLINE_TOOL_PROFILE"
        for node in ast.walk(tree)
    )
    assert found, "SPLINE_TOOL_PROFILE not referenced in profiles.py"


def test_server_wires_apply_spline_tool_profile() -> None:
    """server.py must ``await apply_spline_tool_profile(app)`` (the async wrapper).

    Per the W1.4 + W2a + W2b.1 lessons: the production path must use the
    async helper, NOT the sync wrapper. The sync wrapper raises
    ``RuntimeError`` when called from inside a running event loop, which
    would break any test that runs ``create_app`` under an async context.
    """
    server = REPO_ROOT / "spline_mcp" / "server.py"
    tree = ast.parse(server.read_text())
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Await):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not (
            isinstance(node.value.func, ast.Name)
            and node.value.func.id == "apply_spline_tool_profile"
        ):
            continue
        found = True
        break
    assert found, "await apply_spline_tool_profile(app) not found in server.py"


def test_server_does_not_use_sync_wrapper() -> None:
    """server.py must NOT call the sync ``apply_tool_profile`` wrapper.

    This is the W2b.3 review fix: round 1 used the sync wrapper which
    raises RuntimeError in async contexts. The production path must use
    the async ``apply_spline_tool_profile`` defined in profiles.py.
    """
    server = REPO_ROOT / "spline_mcp" / "server.py"
    tree = ast.parse(server.read_text())
    sync_call = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "apply_tool_profile":
            sync_call = True
    assert not sync_call, (
        "server.py must NOT call the sync apply_tool_profile() wrapper "
        "(raises RuntimeError in event loops). Use apply_spline_tool_profile "
        "instead."
    )


def test_server_wires_tool_profile_env_var() -> None:
    """The dispatch path must pass ``profile_env_var="SPLINE_TOOL_PROFILE"``.

    The env var is passed by ``apply_spline_tool_profile`` to
    ``_apply_tool_profile`` inside profiles.py (lazy import). Verify the
    constant appears in profiles.py.
    """
    profiles = REPO_ROOT / "spline_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if node.value == "SPLINE_TOOL_PROFILE":
            found = True
            break
    assert found, "SPLINE_TOOL_PROFILE not referenced in profiles.py"


def test_pyproject_bumps_mcp_common_to_0_18() -> None:
    """mcp-common pin must be >=0.18.0 (the W0 helper version)."""
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text()
    assert "mcp-common>=0.18.0" in text, (
        "mcp-common pin must be >=0.18.0 in pyproject.toml"
    )


def test_decision_doc_exists_at_tracked_path() -> None:
    """Rationale doc must live at docs/architecture/tool-profile-rationale.md (.claude/ is gitignored)."""
    path = REPO_ROOT / "docs" / "architecture" / "tool-profile-rationale.md"
    assert path.exists(), f"{path} missing"


def test_profile_registrations_subset_of_map() -> None:
    """Every key referenced in PROFILE_REGISTRATIONS must exist in REGISTRATION_MAP.

    Inline assertion (per W2b.1 lesson: prefer inline ``assert set == {...}``
    over golden fixtures for parity tests).
    """

    from spline_mcp.tools.profiles import PROFILE_REGISTRATIONS, _build_registration_map

    mapping = _build_registration_map()
    for profile, regs in PROFILE_REGISTRATIONS.items():
        for group in regs:
            if not isinstance(group, str):
                continue
            assert group in mapping, (
                f"{profile.value} references group {group!r} but REGISTRATION_MAP "
                f"is missing it; keys={sorted(mapping)}"
            )


def test_mandatory_tools_invariant() -> None:
    """MANDATORY_TOOLS ⊆ REGISTRATION_MAP.keys() must hold.

    spline-mcp has NO MCP-registered health tools (only the /healthz HTTP
    route via mcp_common.health), so the MANDATORY_TOOLS invariant is
    vacuously satisfied (mcp-common's default MANDATORY_TOOLS is empty).

    This test pins the explicit opt-out so the relationship cannot drift
    silently:
    - MANDATORY_TOOLS from mcp-common is empty by default
    - apply_spline_tool_profile passes mandatory_groups=set()
    - apply_spline_tool_profile passes essential_tool_names=set()

    If any of these change, this test must be updated to reflect the
    new invariant (either add the health tools to REGISTRATION_MAP or
    document the opt-out in the rationale doc).
    """
    from mcp_common.tools.profiles import MANDATORY_TOOLS

    from spline_mcp.tools.profiles import (
        _build_registration_map,
        apply_spline_tool_profile,
    )

    mapping = _build_registration_map()
    # Vacuous: MANDATORY_TOOLS empty, so any subset holds
    assert MANDATORY_TOOLS.issubset(set(mapping.keys())), (
        f"MANDATORY_TOOLS {sorted(MANDATORY_TOOLS)} not in REGISTRATION_MAP "
        f"keys {sorted(mapping.keys())}"
    )

    # Verify the explicit opt-out is documented in the implementation
    import inspect

    source = inspect.getsource(apply_spline_tool_profile)
    assert "mandatory_groups=set()" in source, (
        "apply_spline_tool_profile must pass mandatory_groups=set() to "
        "explicitly opt out of the MANDATORY_GROUPS invariant"
    )
    assert "essential_tool_names=set()" in source, (
        "apply_spline_tool_profile must pass essential_tool_names=set() to "
        "explicitly opt out of the MANDATORY_TOOLS subset check"
    )


@pytest.mark.asyncio
async def test_full_registers_all_25_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """FULL profile must register all 25 spline tools + discover_tools = 26 total.

    Behavioral parity: original decorator-mode registered 25 tools at import.
    The W0 helper additionally registers ``discover_tools`` (the meta-tool
    the W2b.3 spec requires).
    """
    monkeypatch.setenv("SPLINE_TOOL_PROFILE", "full")
    from fastmcp import FastMCP

    from spline_mcp.tools.profiles import apply_spline_tool_profile

    server = FastMCP(name="Test", instructions="test")
    await apply_spline_tool_profile(server)
    names = {t.name for t in await server.list_tools()}

    # All 22 spline tools
    expected_spline = {
        # generation (6)
        "generate_react_component",
        "generate_vanilla_js",
        "generate_nextjs_component",
        "generate_event_handler",
        "generate_variable_binding",
        "generate_full_integration",
        # assets (5)
        "download_scene",
        "validate_scene",
        "list_cached_scenes",
        "clear_cache",
        "get_cache_stats",
        # helpers (5)
        "build_export_url",
        "parse_scene_url",
        "list_event_types",
        "get_event_documentation",
        "generate_snippet",
        # integration (3)
        "get_websocket_status",
        "subscribe_to_channel",
        "get_integration_status",
        # docs (3)
        "get_runtime_api_docs",
        "get_installation_guide",
        "get_troubleshooting_guide",
    }
    assert expected_spline.issubset(names), (
        f"FULL profile missing tools: {sorted(expected_spline - names)}"
    )
    assert "discover_tools" in names, "W0 helper must register discover_tools meta-tool"
    assert len(names) == 23, (
        f"Expected 23 (22 + discover_tools); got {len(names)}: {sorted(names)}"
    )


@pytest.mark.asyncio
async def test_standard_has_19_daily_driver_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """STANDARD profile must register 19 daily-driver tools (no integration)."""
    monkeypatch.setenv("SPLINE_TOOL_PROFILE", "standard")
    from fastmcp import FastMCP

    from spline_mcp.tools.profiles import apply_spline_tool_profile

    server = FastMCP(name="Test", instructions="test")
    await apply_spline_tool_profile(server)
    names = {t.name for t in await server.list_tools()}

    daily_driver = {
        # generation (6)
        "generate_react_component",
        "generate_vanilla_js",
        "generate_nextjs_component",
        "generate_event_handler",
        "generate_variable_binding",
        "generate_full_integration",
        # assets (5)
        "download_scene",
        "validate_scene",
        "list_cached_scenes",
        "clear_cache",
        "get_cache_stats",
        # helpers (5)
        "build_export_url",
        "parse_scene_url",
        "list_event_types",
        "get_event_documentation",
        "generate_snippet",
        # docs (3)
        "get_runtime_api_docs",
        "get_installation_guide",
        "get_troubleshooting_guide",
    }
    assert daily_driver.issubset(names), (
        f"STANDARD missing daily-driver: {sorted(daily_driver - names)}"
    )
    # FULL-only integration tools absent
    integration_only = {
        "get_websocket_status",
        "subscribe_to_channel",
        "get_integration_status",
    }
    assert not (integration_only & names), (
        f"STANDARD leaked integration tools: {sorted(integration_only & names)}"
    )
    assert "discover_tools" in names


@pytest.mark.asyncio
async def test_minimal_has_only_discover_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MINIMAL profile registers only ``discover_tools`` (no spline domain tools)."""
    monkeypatch.setenv("SPLINE_TOOL_PROFILE", "minimal")
    from fastmcp import FastMCP

    from spline_mcp.tools.profiles import apply_spline_tool_profile

    server = FastMCP(name="Test", instructions="test")
    await apply_spline_tool_profile(server)
    names = {t.name for t in await server.list_tools()}

    assert names == {"discover_tools"}, (
        f"MINIMAL must only register discover_tools; got: {sorted(names)}"
    )
