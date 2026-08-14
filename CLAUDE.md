# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For a shorter, tool-neutral bootstrap document, start with `AGENTS.md`.

## Project Overview

Spline MCP Server is a Model Context Protocol server for orchestrating Spline.design 3D scenes. It provides tools for managing 3D objects, materials, events, and runtime state.

## Ecosystem Context

Part of the **Bodai Ecosystem**:

| Component | Role | Port |
|-----------|------|------|
| Mahavishnu | Orchestrator | 8680 |
| Akosha | Seer | 8682 |
| Dhara | Curator | 8683 |
| Session-Buddy | Builder | 8678 |
| Crackerjack | Inspector | 8676 |
| **spline-mcp** | 3D Orchestrator | 3048 |

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
spline-mcp serve --http --port 3048

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
