"""Next.js generator with SSR support."""

from __future__ import annotations

from spline_mcp.generators.base import (
    CodeGenerator,
    EventHandler,
    GenerationOptions,
    VariableBinding,
)


class NextJSGenerator(CodeGenerator):
    """Generate Next.js components with SSR/SSG support."""

    def generate_component(
        self,
        scene_url: str,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate Next.js component with SSR support."""
        opts = options or self.options
        indent = self._get_indent

        # Generate dynamic import for Spline (required for Next.js)
        dynamic_import = self._generate_dynamic_import(opts)

        # Build props interface
        props_interface = ""
        props_destructure = "{ className, style, onError, onLoad }"

        if opts.typescript:
            props_interface = f"""interface {opts.component_name}Props {{
  className?: string;
  style?: React.CSSProperties;
  onError?: (error: Error) => void;
  onLoad?: () => void;
}}

"""
            props_destructure = f"{{ className, style, onError, onLoad }}: {opts.component_name}Props"

        # Build event handlers
        event_setup = self._build_event_handlers(opts)

        # Build WebSocket integration
        websocket_setup = self._build_websocket_integration(opts)

        # Build component body
        component_body = self._build_component_body(scene_url, opts)

        # Generate SSR placeholder if enabled
        ssr_placeholder = ""
        if opts.ssr_placeholder:
            ssr_placeholder = self._generate_ssr_placeholder(opts)

        # Assemble component
        component = f"""'use client';

import React, {{ Suspense, useRef, useCallback, useState }} from 'react';
{dynamic_import}
{props_interface}{websocket_setup}{event_setup}
{component_body}

{ssr_placeholder}
"""

        return component.strip()

    def _generate_dynamic_import(self, opts: GenerationOptions) -> str:
        """Generate dynamic import for Spline to avoid SSR issues."""
        return """import dynamic from 'next/dynamic';

const Spline = dynamic(
  () => import('@splinetool/react-spline'),
  { ssr: false }
);"""

    def _build_event_handlers(self, opts: GenerationOptions) -> str:
        """Build event handler setup code."""
        if not opts.event_handlers:
            return f"const handleLoad = useCallback(() => {{ onLoad?.(); }}, [onLoad]);"

        indent = self._get_indent(1)
        lines = [f"const handleLoad = useCallback((splineApp: any) => {{"]

        inner_indent = self._get_indent(2)
        for handler in opts.event_handlers:
            target_filter = ""
            if handler.target_object:
                target_filter = f"if (e.target.name === '{handler.target_object}') {{ {handler.handler_code} }}"
            else:
                target_filter = handler.handler_code

            lines.append(f"{inner_indent}splineApp.addEventListener('{handler.event_type.value}', (e: any) => {{")
            lines.append(f"{inner_indent}  {target_filter}")
            lines.append(f"{inner_indent}}});")

        lines.append(f"{inner_indent}setIsLoading(false);")
        lines.append(f"{inner_indent}onLoad?.();")
        lines.append(f"{indent}}}, [onLoad]);")

        return "\n".join(lines)

    def _build_websocket_integration(self, opts: GenerationOptions) -> str:
        """Build WebSocket integration for Next.js."""
        if not opts.include_websocket:
            return ""

        ws_url = opts.websocket_url or "ws://localhost:8690"
        indent = self._get_indent(1)

        return f"""// WebSocket integration with soft failover
const useSplineWebSocket = (url: string = '{ws_url}') => {{
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {{
    try {{
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {{
        setIsConnected(true);
        wsRef.current?.send(JSON.stringify({{ type: 'subscribe', channel: 'spline:variables' }}));
      }};

      wsRef.current.onerror = () => {{
        console.warn('WebSocket unavailable, continuing without real-time updates');
      }};

      wsRef.current.onclose = () => setIsConnected(false);
    }} catch {{
      console.warn('WebSocket not available');
    }}

    return () => wsRef.current?.close();
  }}, [url]);

  const subscribe = useCallback((channel: string, handler: (data: any) => void) => {{
    if (!wsRef.current) return () => {{}};

    const listener = (event: MessageEvent) => {{
      const data = JSON.parse(event.data);
      if (data.channel === channel) handler(data.payload);
    }};

    wsRef.current.addEventListener('message', listener);
    return () => wsRef.current?.removeEventListener('message', listener);
  }}, []);

  return {{ isConnected, subscribe }};
}};

"""

    def _build_component_body(
        self,
        scene_url: str,
        opts: GenerationOptions,
    ) -> str:
        """Build the main component body."""
        indent = self._get_indent(1)

        # State setup
        state_lines = [
            f"{indent}const [isLoading, setIsLoading] = useState(true);",
        ]

        if opts.include_error_boundary:
            state_lines.append(f"{indent}const [hasError, setHasError] = useState(false);")

        # WebSocket hook if enabled
        ws_hook = ""
        if opts.include_websocket:
            ws_hook = f"{indent}const {{ isConnected, subscribe }} = useSplineWebSocket();"

        # Error handler
        error_handler = ""
        if opts.include_error_boundary:
            error_handler = f"""
{indent}const handleError = useCallback((error: Error) => {{
{indent}  setHasError(true);
{indent}  setIsLoading(false);
{indent}  onError?.(error);
{indent}}}, [onError]);
"""

        # Error check
        error_check = ""
        if opts.include_error_boundary:
            error_check = f"""
{indent}if (hasError) {{
{indent}  return (
{indent}    <div className="spline-error" role="alert">
{indent}      Failed to load 3D scene
{indent}    </div>
{indent}  );
{indent}}}
"""

        # Main component
        spline_props = [f'scene="{scene_url}"', "onLoad={handleLoad}"]
        if opts.include_error_boundary:
            spline_props.append("onError={handleError}")
        spline_props.append("className={className}")
        spline_props.append("style={style}")

        body = f"""
{indent}return (
{indent}  <Suspense fallback={{<{opts.component_name}Placeholder />}}>
{indent}    <Spline
{indent}      {' '.join(spline_props)}
{indent}    />
{indent}  </Suspense>
{indent});"""

        # Component wrapper
        props_param = "{ className, style, onError, onLoad }"
        if opts.typescript:
            props_param = f"{{ className, style, onError, onLoad }}: {opts.component_name}Props"

        return f"""export function {opts.component_name}({props_param}) {{
{chr(10).join(state_lines)}
{ws_hook}{error_handler}{error_check}{body}
}}"""

    def _generate_ssr_placeholder(self, opts: GenerationOptions) -> str:
        """Generate SSR placeholder component."""
        indent = self._get_indent(1)

        return f"""function {opts.component_name}Placeholder() {{
{indent}return (
{indent}  <div
{indent}    className="spline-placeholder"
{indent}    style={{
{indent}      display: 'flex',
{indent}      alignItems: 'center',
{indent}      justifyContent: 'center',
{indent}      minHeight: '400px',
{indent}      background: '#f5f5f5'
{indent}    }}
{indent}  >
{indent}    <div>Loading 3D scene...</div>
{indent}  </div>
{indent});
}}"""

    def generate_event_handler(
        self,
        handler: EventHandler,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate standalone event handler code."""
        target_filter = ""
        if handler.target_object:
            target_filter = f"if (e.target.name === '{handler.target_object}') "

        return f"""splineApp.addEventListener('{handler.event_type.value}', (e: any) => {{
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
            value = var.value_source if var.value_source else repr(var.value)
            lines.append(f"  {var.name}: {value},")

        lines.append("};")
        lines.append("")
        lines.append("splineApp.setVariables(variables);")

        return "\n".join(lines)

    def generate_install_instructions(self) -> str:
        """Generate installation instructions."""
        return """npm install @splinetool/react-spline @splinetool/runtime next

# Ensure you have the 'use client' directive at the top of your component
# The dynamic import handles SSR compatibility automatically"""

    def generate_usage_example(
        self,
        component_name: str,
        scene_url: str,
    ) -> str:
        """Generate usage example."""
        lines = [
            f"// app/components/{component_name}.tsx",
            f"import {{ {component_name} }} from './components/{component_name}';",
            "",
            "// In a page or layout",
            "export default function Page() {",
            "  return (",
            "    <main>",
            f"      <{component_name}",
            "        className=\"hero-scene\"",
            "        style={{ height: '100vh' }}}}",
            "        onError={{(e) => console.error(e)}}",
            "        onLoad={{() => console.log('Loaded!')}}",
            "      />",
            "    </main>",
            "  );",
            "}",
        ]
        return "\n".join(lines)
