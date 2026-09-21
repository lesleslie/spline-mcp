# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For a shorter, tool-neutral bootstrap document, start with `AGENTS.md`.

## Project Overview

Spline MCP Server is a Model Context Protocol server for orchestrating Spline.design 3D scenes. It provides tools for managing 3D objects, materials, events, and runtime state. The
**`spline-mcp`** component owns port **3052** (see `spline_mcp/__init__.py`
`DEFAULT_PORT`).

## Development Commands

### Setup

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Testing

```bash
pytest
pytest --cov=spline_mcp --cov-report=html
```

### Code Quality

```bash
ruff format spline_mcp/
ruff check spline_mcp/
mypy spline_mcp/
```

### MCP Server

```bash
# Stdio mode
spline-mcp serve

# HTTP mode
spline-mcp serve --http --port 3052

# Health check
spline-mcp health
```

## Architecture

```
spline_mcp/
├── __init__.py          # Package metadata
├── cli.py               # Typer CLI commands
├── config.py            # Oneiric-based configuration
├── server.py            # FastMCP application
├── client.py            # Spline API client (placeholder)
├── assets/              # Asset management
├── generators/          # Code generation (React, Vanilla, Next.js)
├── integrations/        # External integrations
└── tools/               # MCP tool definitions
    ├── __init__.py      # Tool registration helpers
    ├── generation.py    # Code generation tools (6)
    ├── assets.py        # Asset management tools (5)
    ├── helpers.py       # Utility tools (5)
    ├── integration.py   # Integration tools (6)
    └── docs.py          # Documentation tools (3)
```

## Key Patterns

### Oneiric Configuration

Settings loaded from:

1. Default values in `SplineSettings`
1. `settings/spline-mcp.yaml`
1. `settings/local.yaml` (gitignored)
1. Environment variables `SPLINE_*`

### FastMCP Tool Registration

Tools are registered in dedicated modules:

```python
def register_scene_tools(app: FastMCP) -> None:
    @app.tool()
    async def list_scenes() -> list[dict[str, Any]]:
        # Implementation
```

### Tool Profile System

`create_app()` dispatches the 5 `register_*_tools()` groups via the W0
helper from `mcp-common>=0.18.0`, gated by `SPLINE_TOOL_PROFILE`:

| Profile | Groups | Tool count |
|-----------|-----------------------------------------------------|------------|
| MINIMAL | (none) | 0 + discover_tools |
| STANDARD | assets, generation, helpers, docs | 19 + discover_tools |
| FULL | assets, generation, helpers, docs, integration | 25 + discover_tools |

Default (unset) is FULL. See `docs/architecture/tool-profile-rationale.md`
for the mapping rationale and `spline_mcp/tools/profiles.py` for the
dispatch surface.

### Async Client Pattern

```python
async with SplineClient(api_key, base_url) as client:
    scene = await client.get_scene(scene_id)
```

## Configuration Files

- `settings/spline-mcp.yaml` - Main configuration (committed)
- `settings/local.yaml` - Local overrides (gitignored)
- `.env` - Environment secrets (gitignored)

## API Reference

The Spline scene/object/material/event abstractions live alongside the runtime
helpers, not in a single client class:

- `spline_mcp/assets/manager.py` — `SplineAssetManager`, `SplineSceneMetadata` (download, cache, list)
- `spline_mcp/assets/validator.py` — `validate_scene_file` (scene-file integrity checks)
- `spline_mcp/generators/base.py` — `SplineEventType`, framework-agnostic generation types
- `spline_mcp/tools/*.py` — public MCP tool surface (see Architecture above)

`spline_mcp/client.py` is a thin placeholder; reach for the modules above
when adding new scene/object/material behavior.

## Bodai integration

When installed alongside the [Bodai ecosystem](https://github.com/lesleslie/bodai),
spline-mcp participates as the 3D scene orchestration component. The
**`spline-mcp`** component owns port **3052** and integrates with
Mahavishnu's WebSocket infrastructure for real-time event broadcasting
(see `spline_mcp/integrations/websocket.py`). No Bodai-specific code is
imported at runtime — integration is via the shared mcp-common substrate
and the Mahavishnu WebSocket URL configured in `settings/spline-mcp.yaml`.
