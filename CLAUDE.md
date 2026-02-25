# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spline MCP Server is a Model Context Protocol server for orchestrating Spline.design 3D scenes. It provides tools for managing 3D objects, materials, events, and runtime state.

## Ecosystem Context

Part of the **Bodai Ecosystem**:

| Component | Role | Port |
|-----------|------|------|
| Mahavishnu | Orchestrator | 8680 |
| Akosha | Seer | 8682 |
| Dhruva | Curator | 8683 |
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
├── client.py            # Spline API client
└── tools/
    ├── __init__.py      # Tool registration
    ├── scenes.py        # Scene management (4 tools)
    ├── objects.py       # Object CRUD (5 tools)
    ├── materials.py     # Material system (3 tools)
    ├── events.py        # Event management (3 tools)
    └── runtime.py       # Runtime API (3 tools)
```

## Key Patterns

### Oneiric Configuration

Settings loaded from:
1. Default values in `SplineSettings`
2. `settings/spline.yaml`
3. `settings/local.yaml` (gitignored)
4. Environment variables `SPLINE_*`

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

- `settings/spline.yaml` - Main configuration (committed)
- `settings/local.yaml` - Local overrides (gitignored)
- `.env` - Environment secrets (gitignored)

## API Reference

See `spline_mcp/client.py` for the full SplineClient implementation with typed models:

- `SplineScene` - Scene representation
- `SplineObject` - 3D object model
- `SplineMaterial` - Material definition
- `SplineEvent` - Event configuration
