# spline-mcp

MCP server for [Spline.design](https://spline.design) 3D scene orchestration.

## Installation

```bash
uv pip install -e .
```

## Configuration

Set your Spline API key as an environment variable:

```bash
export SPLINE_API_KEY="your-api-key-here"
```

Or create a `.env` file:

```
SPLINE_API_KEY=your-api-key-here
```

## Usage

### Stdio Mode (default)

```bash
spline-mcp serve
```

### HTTP Mode

```bash
spline-mcp serve --http --port 3048
```

### Health Check

```bash
spline-mcp health
```

## Available Tools

### Scene Management

| Tool | Description |
|------|-------------|
| `list_scenes` | List all accessible scenes |
| `get_scene` | Get scene details by ID |
| `create_scene` | Create a new scene |
| `delete_scene` | Delete a scene |

### Object Management

| Tool | Description |
|------|-------------|
| `list_objects` | List all objects in a scene |
| `get_object` | Get object details |
| `create_object` | Create a new 3D object |
| `update_object` | Update object properties |
| `delete_object` | Delete an object |

### Material System

| Tool | Description |
|------|-------------|
| `list_materials` | List all materials in a scene |
| `create_material` | Create a new material |
| `apply_material` | Apply material to an object |

### Events & Actions

| Tool | Description |
|------|-------------|
| `list_events` | List all events in a scene |
| `create_event` | Create a new event |
| `trigger_event` | Manually trigger an event |

### Runtime API

| Tool | Description |
|------|-------------|
| `get_runtime_state` | Get current runtime state |
| `set_variable` | Set a runtime variable |
| `export_scene` | Export scene to file format |

## Configuration Options

Set via environment variables with `SPLINE_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `SPLINE_API_KEY` | - | Spline API authentication key |
| `SPLINE_API_BASE_URL` | `https://api.spline.design/v1` | API base URL |
| `SPLINE_API_TIMEOUT` | `30.0` | Request timeout in seconds |
| `SPLINE_DEFAULT_SCENE_ID` | - | Default scene for operations |
| `SPLINE_AUTO_SAVE` | `true` | Auto-save after modifications |
| `SPLINE_HTTP_HOST` | `127.0.0.1` | HTTP server host |
| `SPLINE_HTTP_PORT` | `3048` | HTTP server port |
| `SPLINE_LOG_LEVEL` | `INFO` | Logging level |
| `SPLINE_LOG_JSON` | `true` | Use JSON logging format |

## Architecture

Built with the Bodai ecosystem stack:

- **FastMCP**: MCP protocol implementation
- **Oneiric**: Configuration management
- **mcp-common**: Shared utilities
- **Pydantic**: Data validation
- **httpx**: Async HTTP client

## License

BSD-3-Clause
