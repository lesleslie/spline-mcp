# spline-mcp

[![Code style: crackerjack](https://img.shields.io/badge/code%20style-crackerjack-000042)](https://github.com/lesleslie/crackerjack)
[![Runtime: oneiric](https://img.shields.io/badge/runtime-oneiric-6e5494)](https://github.com/lesleslie/oneiric)
[![Framework: FastMCP](https://img.shields.io/badge/framework-FastMCP-0ea5e9)](https://github.com/PrefectHQ/fastmcp)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python: 3.13+](https://img.shields.io/badge/python-3.13%2B-green)](https://www.python.org/downloads/)

MCP server for [Spline.design](https://spline.design) code generation and asset management.

## Overview

Spline.design is a 3D design tool that exports interactive scenes for the web. This MCP server provides:

- **Code Generation**: Generate React, Next.js, and vanilla JS integration code
- **Asset Management**: Download, cache, and validate `.splinecode` files
- **Integration Support**: WebSocket (Mahavishnu) integration
- **Helper Utilities**: URL building, event documentation, code snippets

> **Note**: Spline does not have a traditional REST API. Scenes are created in the Spline editor and exported as `.splinecode` files for runtime use.

## Spline V2 Compatibility

Spline V2 (released August 20, 2026) ships its own MCP server inside the rebuilt Spline desktop app that lets AI agents drive the editor directly — creating and modifying objects, materials, lights, cameras, booleans, particles, cloners, lathes, sky, variables, events, and states. See the [Spline V2 launch announcement](https://blog.spline.design/spline-v2) for details.

This server fills a **different, complementary niche**:

| Workflow stage | Tool |
|---|---|
| **Authoring** — building / editing the scene in the editor | [Spline V2 MCP](https://blog.spline.design/spline-v2) (bundled with the Spline desktop app) |
| **Embedding** — putting the exported scene into your React / Next.js / vanilla app | **This server** (`spline-mcp`) |
| **Runtime control** — manipulating variables / events from your app at runtime | Both cooperate: V2 MCP builds the scene; this server emits the JS that drives `setNumberVariable()` / `emitEvent()` from the host app |

Concretely, this server does **not** edit scenes — it operates strictly on already-exported `.splinecode` URLs. If you need an agent to author a new scene from scratch, install the [Spline desktop app](https://spline.design) and use its built-in MCP server. Use **this server** when you have a published `.splinecode` URL and want to scaffold the React / Next.js / vanilla integration, cache the scene asset, wire up runtime event handlers, or pipe events into Mahavishnu.

## Installation

```bash
uv pip install -e .
```

## Quick Start

### Generate a React Component

```bash
spline-mcp generate react https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode
```

### Download a Scene

```bash
spline-mcp download https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode
```

## MCP Server Usage

### Stdio Mode (default)

```bash
spline-mcp serve
```

### HTTP Mode

```bash
spline-mcp serve --http --port 3048
```

## Available Tools

### Code Generation

| Tool | Description |
|------|-------------|
| `generate_react_component` | Generate React component with TypeScript |
| `generate_vanilla_js` | Generate standalone HTML/JS |
| `generate_nextjs_component` | Generate Next.js component with SSR support |
| `generate_event_handler` | Generate event handler code |
| `generate_variable_binding` | Generate runtime variable bindings |
| `generate_full_integration` | Complete integration with all features |

### Asset Management

| Tool | Description |
|------|-------------|
| `download_scene` | Download and cache a .splinecode file |
| `validate_scene` | Validate a .splinecode file |
| `list_cached_scenes` | List all cached scenes |
| `clear_cache` | Clear cached scenes |
| `get_cache_stats` | Get cache statistics |

### Helper Utilities

| Tool | Description |
|------|-------------|
| `build_export_url` | Build export URL from scene ID |
| `parse_scene_url` | Parse URL to extract scene ID |
| `list_event_types` | List supported Spline event types |
| `get_event_documentation` | Get docs for specific event |
| `generate_snippet` | Generate common code snippets |

### Integration

| Tool | Description |
|------|-------------|
| `get_websocket_status` | Check Mahavishnu WebSocket connection |
| `subscribe_to_channel` | Subscribe to real-time updates |
| `get_integration_status` | Status of all integrations |
| `get_integration_status` | Status of all integrations |

### Documentation

| Tool | Description |
|------|-------------|
| `get_runtime_api_docs` | Get documentation for the @splinetool/runtime API by topic |
| `get_installation_guide` | Get installation guide for the Spline runtime |
| `get_troubleshooting_guide` | Get troubleshooting guide for common Spline issues |

## Configuration

Set via environment variables with `SPLINE_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `SPLINE_DEFAULT_FRAMEWORK` | `react` | Default framework (react/vanilla/nextjs) |
| `SPLINE_TYPESCRIPT` | `true` | Generate TypeScript code |
| `SPLINE_LAZY_LOAD` | `true` | Use lazy loading with Suspense |
| `SPLINE_SSR_PLACEHOLDER` | `false` | Generate SSR placeholder for Next.js |
| `SPLINE_INDENT_SPACES` | `2` | Indentation spaces for generated code (2-8) |
| `SPLINE_SEMICOLONS` | `true` | Use semicolons in generated JavaScript |
| `SPLINE_CACHE_DIR` | `~/.spline-mcp/cache` | Cache directory |
| `SPLINE_MAX_CACHE_SIZE_MB` | `500` | Maximum cache size |
| `SPLINE_AUTO_VALIDATE` | `true` | Automatically validate downloaded scenes |
| `SPLINE_WEBSOCKET_ENABLED` | `true` | Enable WebSocket integration |
| `SPLINE_WEBSOCKET_URL` | `ws://localhost:8690` | Mahavishnu WebSocket URL |
| `SPLINE_WEBSOCKET_AUTO_RECONNECT` | `true` | Automatically reconnect on disconnect |
| `SPLINE_ENABLE_HTTP_TRANSPORT` | `false` | Enable HTTP transport |
| `SPLINE_HTTP_HOST` | `127.0.0.1` | HTTP server host |
| `SPLINE_HTTP_PORT` | `3048` | HTTP server port |
| `SPLINE_LOG_LEVEL` | `INFO` | Logging level |
| `SPLINE_LOG_JSON` | `true` | Use JSON logging format |

## Generated Code Examples

### React Component

```tsx
import { Suspense, useRef, useCallback } from 'react';
import Spline from '@splinetool/react-spline';

interface HeroSceneProps {
  className?: string;
}

export function HeroScene({ className }: HeroSceneProps) {
  return (
    <Suspense fallback={<div>Loading 3D scene...</div>}>
      <Spline
        scene="https://prod.spline.design/xxx/scene.splinecode"
        className={className}
      />
    </Suspense>
  );
}
```

### With WebSocket Integration

```tsx
// Auto-generated WebSocket integration with soft failover
const { subscribe, isConnected } = useWebSocket('ws://localhost:8690');

useEffect(() => {
  if (!isConnected) return;

  const unsubscribe = subscribe('spline:variables', (data) => {
    splineRef.current?.setVariables(data);
  });

  return unsubscribe;
}, [isConnected]);
```

## Architecture

```
spline_mcp/
├── generators/         # Code generation (React, Vanilla, Next.js)
│   ├── base.py         # Base classes and types
│   ├── react.py        # React generator with FastBlocks patterns
│   ├── vanilla.py      # Vanilla JS/HTML generator
│   └── nextjs.py       # Next.js SSR generator
├── assets/             # Asset management
│   ├── manager.py      # Download, cache, validate
│   └── validator.py    # Scene file validation
├── integrations/       # External integrations
│   └── websocket.py    # Mahavishnu WebSocket (soft failover)
├── tools/              # MCP tool definitions
│   ├── generation.py   # Code generation tools
│   ├── assets.py       # Asset management tools
│   ├── helpers.py      # Utility tools
│   └── integration.py  # Integration tools
├── config.py           # Oneiric-based configuration
└── server.py           # FastMCP application
```

## Ecosystem Integration

Part of the **Bodai Ecosystem**:

| Component | Role | Port |
|-----------|------|------|
| Mahavishnu | Orchestrator | 8680 |
| Akosha | Seer | 8682 |
| Dhara | Curator | 8683 |
| Session-Buddy | Builder | 8678 |
| Crackerjack | Inspector | 8676 |
| **spline-mcp** | 3D Orchestrator | 3048 |

## Installation via Bodai Marketplace

This repo ships a Bodai Claude Code plugin manifest (`.claude-plugin/plugin.json`) plus a colocated `.mcp.json` and three slash commands in `commands/`. To install via the Bodai marketplace, first register the marketplace with Claude Code, then install the plugin by name. Once installed, the slash commands `/spline-generate`, `/spline-assets`, and `/spline-websocket` become available alongside the `mcp__spline__*` tools. Make sure the spline-mcp HTTP server is running on its configured port before invoking the slash commands.

## License

BSD-3-Clause
