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

| Profile   | Groups registered                              | Tool count |
|-----------|------------------------------------------------|------------|
| MINIMAL   | (none)                                         | 0 + discover_tools |
| STANDARD  | assets, generation, helpers, docs              | 19 + discover_tools |
| FULL      | assets, generation, helpers, docs, integration | 25 + discover_tools |

Rationale per tier:

- **MINIMAL** — Reserve the profile for HTTP `/healthz`-only deployments
  (no domain tools exposed). Default behavior at `SPLINE_TOOL_PROFILE=""`
  or unset is FULL (per spec).
- **STANDARD** — The daily-driver set: scene CRUD (assets), code
  import/export (generation), URL utilities (helpers), API reference
  (docs). Excludes FULL-only WebSocket/n8n integrations that depend on
  external services being configured.
- **FULL** — All 25 tools. The previous behavior.

The W0 helper additionally registers `discover_tools`, a meta-tool that
filters the registered tool list by query. This is preserved across all
profiles.

## Wiring

`create_app()` in `spline_mcp/server.py` replaces the 5 explicit
`register_*_tools(app)` calls with a single `apply_tool_profile(app, ...)`
invocation passing:

- `profile_env_var="SPLINE_TOOL_PROFILE"`
- `registrations=PROFILE_REGISTRATIONS` from `spline_mcp/tools/profiles.py`
- `registration_map=_build_registration_map()` (lazy import)
- `register_all_fn=register_all_tool_groups`

The sync `apply_tool_profile` wrapper calls `asyncio.run()` internally,
which works at module import time (no event loop running). Tests that
need to drive the dispatch from an async context use the async
`apply_spline_tool_profile` helper defined in `spline_mcp/tools/profiles.py`.

## Migration

Pre-refactor (5 inline calls):

```python
register_generation_tools(app)
register_asset_tools(app)
register_helper_tools(app)
register_integration_tools(app)
register_docs_tools(app)
```

Post-refactor (1 dispatch call):

```python
apply_tool_profile(
    app,
    profile_env_var="SPLINE_TOOL_PROFILE",
    registrations=PROFILE_REGISTRATIONS,
    registration_map=_build_registration_map(),
    register_all_fn=register_all_tool_groups,
)
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

`tests/test_tool_profile.py` adds 11 wiring tests:

- 8 AST-level pinning tests (profiles.py structure, server.py wiring,
  pyproject pin, rationale doc)
- 1 inline subset parity test (REGISTRATION_MAP keys cover all profile
  references)
- 3 behavioral parity tests (FULL=26, STANDARD=20, MINIMAL=1) using
  `monkeypatch.setenv("SPLINE_TOOL_PROFILE", ...)` for env isolation

`tests/test_server.py::TestServerCreation::test_create_app_registers_tools`
was updated to mock `apply_tool_profile` instead of the 5 individual
register_*_tools functions (the latter no longer exist in
`spline_mcp.server`).

## Notes for downstream consumers

- `mcp-common>=0.18.0` is required (was `>=0.16.4`).
- The `discover_tools` meta-tool is now always registered.
- Operators that previously relied on all 25 tools being exposed should
  leave `SPLINE_TOOL_PROFILE` unset (defaults to FULL).
