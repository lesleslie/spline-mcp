# spline-mcp Tool Profile Adoption

**Status:** W2b.3 (Tier-C trivial mapping)

**Date:** 2026-08-18

## Context

spline-mcp is a 25-tool FastMCP server for Spline.design code generation
and asset management. The W0 helper from `mcp-common>=0.18.0` reduces
context-token load by gating which `register_*_tools()` groups are called
at startup based on the `SPLINE_TOOL_PROFILE` environment variable.

The W2b.3 task is the smallest Tier-C adoption: only 5 register fns
across 5 files (`spline_mcp/tools/{generation,assets,helpers,docs,integration}.py`).

## Decision

Three-tier profile mapping:

| Profile | Groups registered | Tool count |
|-----------|------------------------------------------------|------------|
| MINIMAL | (none) | 0 + discover_tools |
| STANDARD | assets, generation, helpers, docs | 19 + discover_tools |
| FULL | assets, generation, helpers, docs, integration | 25 + discover_tools |

Rationale per tier:

- **MINIMAL** — Reserve the profile for HTTP `/healthz`-only deployments
  (no domain tools exposed). Default behavior at `SPLINE_TOOL_PROFILE=""`
  or unset is FULL (per spec).
- **STANDARD** — The daily-driver set: scene CRUD (assets), code
  import/export (generation), URL utilities (helpers), API reference
  (docs). Excludes FULL-only WebSocket integrations that depend on
  external services being configured.
- **FULL** — All 25 tools. The previous behavior.

The W0 helper additionally registers `discover_tools`, a meta-tool that
filters the registered tool list by query. This is preserved across all
profiles.

## Wiring

`create_app()` in `spline_mcp/server.py` is **async** and delegates
the tool profile dispatch to `apply_spline_tool_profile(app)` (the
async wrapper) before returning the FastMCP app:

```python
async def create_app() -> FastMCP:
    settings = get_settings()
    setup_logging(settings)
    ...
    app = FastMCP(name=APP_NAME, version=APP_VERSION)
    register_http_health_route(app, ...)
    _attach_otel_middleware(app)
    await apply_spline_tool_profile(app)   # async helper
    return app


def get_app() -> FastMCP:
    global _app
    if _app is None:
        _app = asyncio.run(create_app())  # sync → async bridge
    return _app
```

The async dispatch is required because the W0 helper
(`mcp_common.tools.dispatch._apply_tool_profile`) is async. Per the
W1.4 + W2a + W2b.1 lessons, the sync wrapper `apply_tool_profile()` raises
`RuntimeError` when called from inside a running event loop, so the
async path is the only correct path for both production and any
integration that runs under an asyncio loop.

`apply_spline_tool_profile` (defined in `spline_mcp/tools/profiles.py`)
forwards to `_apply_tool_profile` with:

- `profile_env_var="SPLINE_TOOL_PROFILE"`
- `registrations=PROFILE_REGISTRATIONS` (from `spline_mcp/tools/profiles.py`)
- `registration_map=_build_registration_map()` (lazy import)
- `register_all_fn=register_all_tool_groups`
- `mandatory_groups=set()` (no MCP health tools — see below)
- `essential_tool_names=set()` (no MCP health tools — see below)

## MANDATORY_TOOLS invariant

`mcp-common` defines `MANDATORY_GROUPS` (default empty) and
`MANDATORY_TOOLS` (default empty). The W0 helper's `_apply_tool_profile`
performs a subset check `MANDATORY_TOOLS ⊆ registered_tools` after
dispatch.

spline-mcp has **no MCP-registered health tools** — only the `/healthz`
HTTP route via `mcp_common.health.register_http_health_route` (which
registers a Starlette endpoint, not an MCP tool). The `MANDATORY_TOOLS`
invariant is therefore vacuously satisfied.

The explicit opt-out is documented in `apply_spline_tool_profile`:

```python
await _apply_tool_profile(
    server,
    ...
    mandatory_groups=set(),          # explicit opt-out
    essential_tool_names=set(),     # explicit opt-out
)
```

If spline-mcp adds MCP health tools in the future, add them to the
registration map and pass them via `mandatory_groups` + `essential_tool_names`
to enforce the invariant.

## Migration

Pre-refactor (5 inline calls):

```python
register_generation_tools(app)
register_asset_tools(app)
register_helper_tools(app)
register_integration_tools(app)
register_docs_tools(app)
```

Post-refactor (1 async dispatch call):

```python
await apply_spline_tool_profile(app)
```

The `Tools registered` log line was removed — the W0 helper logs
`Applied <env>=<profile> → N tools registered`, which is more useful
(context-aware count) than the previous hardcoded list.

## Bootstrap behaviors audited

All 5 register fns perform pure tool registration via `@app.tool()`
decorators — no banner, no module-level side effects, no startup hooks.
Replacing them with the W0 helper is behavior-preserving.

The CLI banner (`Starting stdio MCP server`) lives in `spline_mcp/cli.py`
and is independent of the tool registry — no gating needed.

## Tests

`tests/test_tool_profile.py` adds 15 wiring tests:

- 10 AST-level pinning tests (profiles.py structure, server.py wiring,
  pyproject pin, rationale doc, sync-wrapper prohibition, env-var
  presence in profiles.py)
- 1 inline subset parity test (REGISTRATION_MAP keys cover all profile
  references)
- 1 MANDATORY_TOOLS invariant test (vacuously satisfied; explicit opt-out
  is asserted via `inspect.getsource`)
- 3 behavioral parity tests (full / standard / minimal coverage)

The round 1 review fix is verified by:

- `tests/test_tool_profile.py::test_server_wires_apply_spline_tool_profile`
  — asserts `await apply_spline_tool_profile(app)` is in server.py
- `tests/test_tool_profile.py::test_server_does_not_use_sync_wrapper` —
  asserts the sync wrapper is NOT used in server.py
- `tests/test_server.py::TestServerCreation::test_create_app_registers_tools`
  — real production-path test that exercises the async dispatch and
  verifies the actual tool set. Does NOT mock the dispatch helper.
  This test would fail with `RuntimeError` if the sync wrapper were used.

## Notes for downstream consumers

- `mcp-common>=0.18.0` is required (was `>=0.16.4`).
- The `discover_tools` meta-tool is now always registered.
- Operators that previously relied on all 25 tools being exposed should
  leave `SPLINE_TOOL_PROFILE` unset (defaults to FULL).
- `create_app()` is now async. Sync callers (e.g. `get_app()`) bridge
  via `asyncio.run`. Async callers (e.g. integration tests) can directly
  `await create_app()`.
