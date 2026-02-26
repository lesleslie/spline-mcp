# spline-mcp

MCP server for [Spline.design](https://spline.design) code generation and asset management.

## Overview

Spline.design is a 3D design tool that exports interactive scenes for the web. This MCP server provides:

- **Code Generation**: Generate React, Next.js, and vanilla JS integration code
- **Asset Management**: Download, cache, and validate `.splinecode` files
- **Integration Support**: WebSocket (Mahavishnu) and n8n workflow integration
- **Helper Utilities**: URL building, event documentation, code snippets

> **Note**: Spline does not have a traditional REST API. Scenes are created in the Spline editor and exported as `.splinecode` files for runtime use.

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
| `get_n8n_status` | Check n8n availability |
| `generate_n8n_workflow` | Generate n8n workflow for Spline |
| `trigger_n8n_webhook` | Trigger n8n webhook |
| `get_integration_status` | Status of all integrations |

## Configuration

Set via environment variables with `SPLINE_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `SPLINE_DEFAULT_FRAMEWORK` | `react` | Default framework (react/vanilla/nextjs) |
| `SPLINE_TYPESCRIPT` | `true` | Generate TypeScript code |
| `SPLINE_LAZY_LOAD` | `true` | Use lazy loading with Suspense |
| `SPLINE_CACHE_DIR` | `~/.spline-mcp/cache` | Cache directory |
| `SPLINE_MAX_CACHE_SIZE_MB` | `500` | Maximum cache size |
| `SPLINE_WEBSOCKET_ENABLED` | `true` | Enable WebSocket integration |
| `SPLINE_WEBSOCKET_URL` | `ws://localhost:8690` | Mahavishnu WebSocket URL |
| `SPLINE_N8N_ENABLED` | `true` | Enable n8n integration |
| `SPLINE_N8N_URL` | `http://localhost:3044` | n8n server URL |
| `SPLINE_HTTP_PORT` | `3048` | HTTP server port |
| `SPLINE_LOG_LEVEL` | `INFO` | Logging level |

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
│   ├── websocket.py    # Mahavishnu WebSocket (soft failover)
│   └── n8n.py          # n8n workflow integration
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
| Dhruva | Curator | 8683 |
| Session-Buddy | Builder | 8678 |
| Crackerjack | Inspector | 8676 |
| **spline-mcp** | 3D Orchestrator | 3048 |

## License

BSD-3-Clause
