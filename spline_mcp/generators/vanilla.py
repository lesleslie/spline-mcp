"""Vanilla JavaScript generator for Spline scenes."""

from __future__ import annotations

from spline_mcp.generators.base import (
    CodeGenerator,
    EventHandler,
    GenerationOptions,
    VariableBinding,
)


class VanillaJSGenerator(CodeGenerator):
    """Generate vanilla JavaScript integration code."""

    def generate_component(
        self,
        scene_url: str,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate vanilla JavaScript/HTML for the Spline scene."""
        opts = options or self.options
        indent = self._get_indent

        # Build event handlers
        event_handlers = self._build_event_handlers_code(opts)

        # Build variable setup
        variable_setup = self._build_variable_setup_code(opts)

        # Build WebSocket integration
        websocket_code = self._build_websocket_code(opts)

        # Generate complete HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Spline 3D Scene</title>
  <style>
    #canvas-container {{
      width: 100%;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .spline-loading {{
      color: #666;
      font-family: system-ui, sans-serif;
    }}
    .spline-error {{
      color: #c00;
      padding: 20px;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div id="canvas-container">
    <div class="spline-loading" id="loading">Loading 3D scene...</div>
    <div class="spline-error" id="error" style="display: none;">
      Failed to load scene. Please try again later.
    </div>
  </div>

  <script type="module">
    import {{ Application }} from 'https://unpkg.com/@splinetool/runtime@1.0.93/build/runtime.js';

    const canvas = document.getElementById('canvas-container');
    const loading = document.getElementById('loading');
    const errorDiv = document.getElementById('error');

    // Initialize Spline application
    const spline = new Application(canvas);
{variable_setup}
{websocket_code}
    // Load the scene
    spline.load('{scene_url}')
      .then(() => {{
        loading.style.display = 'none';
        console.log('Spline scene loaded successfully');
{event_handlers}
      }})
      .catch((err) => {{
        loading.style.display = 'none';
        errorDiv.style.display = 'block';
        console.error('Failed to load Spline scene:', err);
      }});
  </script>
</body>
</html>"""

        return html.strip()

    def _build_event_handlers_code(self, opts: GenerationOptions) -> str:
        """Build event handler registration code."""
        if not opts.event_handlers:
            return f"        // Scene loaded, no event handlers configured"

        lines = []
        for handler in opts.event_handlers:
            target_filter = ""
            if handler.target_object:
                target_filter = f"if (e.target.name === '{handler.target_object}') "

            lines.append(f"        spline.addEventListener('{handler.event_type.value}', (e) => {{")
            lines.append(f"          {target_filter}{{")
            lines.append(f"            {handler.handler_code}")
            lines.append(f"          }}")
            lines.append(f"        }});")

        return "\n".join(lines)

    def _build_variable_setup_code(self, opts: GenerationOptions) -> str:
        """Build variable initialization code."""
        if not opts.variables:
            return ""

        lines = ["    // Initial variables"]
        lines.append("    const initialVariables = {")

        for var in opts.variables:
            value = var.value if var.value is not None else "null"
            if isinstance(value, str):
                value = f"'{value}'"
            lines.append(f"      {var.name}: {value},")

        lines.append("    };")
        lines.append("")

        return "\n".join(lines)

    def _build_websocket_code(self, opts: GenerationOptions) -> str:
        """Build WebSocket integration code for vanilla JS."""
        if not opts.include_websocket:
            return ""

        ws_url = opts.websocket_url or "ws://localhost:8690"

        return f"""    // WebSocket integration (soft failover)
    let ws = null;
    try {{
      ws = new WebSocket('{ws_url}');

      ws.onopen = () => {{
        console.log('WebSocket connected to Mahavishnu');
        ws.send(JSON.stringify({{ type: 'subscribe', channel: 'spline:variables' }}));
      }};

      ws.onmessage = (event) => {{
        const data = JSON.parse(event.data);
        if (data.channel === 'spline:variables' && spline) {{
          spline.setVariables(data.payload);
        }}
      }};

      ws.onerror = (err) => {{
        console.warn('WebSocket connection failed, continuing without real-time updates:', err);
      }};

      ws.onclose = () => {{
        console.log('WebSocket disconnected');
      }};
    }} catch (err) {{
      console.warn('WebSocket not available, continuing without real-time updates');
    }}

"""

    def generate_event_handler(
        self,
        handler: EventHandler,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate standalone event handler code."""
        target_filter = ""
        if handler.target_object:
            target_filter = f"if (e.target.name === '{handler.target_object}') "

        return f"""spline.addEventListener('{handler.event_type.value}', (e) => {{
  {target_filter}{{
    {handler.handler_code}
  }}
}});"""

    def generate_variable_bindings(
        self,
        variables: list[VariableBinding],
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate variable binding code."""
        lines = ["const variables = {"]

        for var in variables:
            value = var.value if var.value is not None else "null"
            if isinstance(value, str):
                value = f"'{value}'"
            lines.append(f"  {var.name}: {value},")

        lines.append("};")
        lines.append("")
        lines.append("spline.setVariables(variables);")

        return "\n".join(lines)

    def generate_install_instructions(self) -> str:
        """Generate installation instructions."""
        return """# Option 1: CDN (no installation needed)
# The generated HTML includes the runtime from unpkg CDN

# Option 2: npm install for self-hosting
npm install @splinetool/runtime

# Option 3: Download .splinecode file for offline use
# Use the spline-mcp asset manager to download and cache scenes"""

    def generate_usage_example(
        self,
        component_name: str,
        scene_url: str,
    ) -> str:
        """Generate usage example."""
        return f"""<!-- Basic usage: Include the generated HTML file directly -->
<script type="module">
  import {{ Application }} from '@splinetool/runtime';

  const spline = new Application(document.getElementById('canvas'));
  await spline.load('{scene_url}');

  // Listen to events
  spline.addEventListener('mouseDown', (e) => {{
    console.log('Clicked:', e.target.name);
  }});

  // Set variables
  spline.setVariable('myColor', '#ff0000');
</script>"""
