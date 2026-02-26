"""React component generator with FastBlocks-style patterns."""

from __future__ import annotations

from spline_mcp.generators.base import (
    CodeGenerator,
    EventHandler,
    GenerationOptions,
    VariableBinding,
)


class ReactGenerator(CodeGenerator):
    """Generate React components with TypeScript support."""

    def generate_component(
        self,
        scene_url: str,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate a React component for the Spline scene."""
        opts = options or self.options
        indent = self._get_indent

        # Build props interface
        props_fields = self._build_props_interface(opts)
        props_destructure = self._build_props_destructure(opts)

        # Build event handlers
        event_setup = self._build_event_handlers(opts)

        # Build variable initialization
        variable_setup = self._build_variable_setup(opts)

        # Build WebSocket integration if enabled
        websocket_setup = self._build_websocket_integration(opts)

        # Build component body
        component_body = self._build_component_body(scene_url, opts)

        # Generate TypeScript interface if needed
        interface_code = ""
        if opts.typescript:
            interface_code = f"interface {opts.component_name}Props {{\n{props_fields}\n}}\n\n"

        # Generate imports
        imports = self._generate_imports(opts)

        # Generate loading fallback
        fallback = self._generate_fallback(opts)

        # Assemble component
        component = f"{imports}\n\n{interface_code}export function {opts.component_name}({props_destructure}) {{\n{websocket_setup}{event_setup}{variable_setup}\n{component_body}\n}}\n\n{fallback}\n"
        return component.strip()

    def _generate_imports(self, opts: GenerationOptions) -> str:
        """Generate import statements."""
        imports = []

        if opts.lazy_load:
            imports.append("import React, {{ Suspense, useRef, useCallback, useState }} from 'react';")
        else:
            imports.append("import React, {{ useRef, useCallback, useState }} from 'react';")

        imports.append("import Spline from '@splinetool/react-spline';")

        if opts.include_websocket:
            imports.append("import {{ useWebSocket }} from '@bodai/mahavishnu-client';")

        return "\n".join(imports)

    def _build_props_interface(self, opts: GenerationOptions) -> str:
        """Build the TypeScript props interface fields."""
        indent = self._get_indent(1)
        fields = [
            f"{indent}className?: string;",
            f"{indent}style?: React.CSSProperties;",
        ]

        if opts.include_error_boundary:
            fields.append(f"{indent}onError?: (error: Error) => void;")

        fields.append(f"{indent}onLoad?: () => void;")

        # Add variable props
        for var in opts.variables:
            if var.value_source:
                var_name = var.name
                fields.append(f"{indent}{var_name}?: unknown;")

        return "\n".join(fields)

    def _build_props_destructure(self, opts: GenerationOptions) -> str:
        """Build the props destructuring pattern."""
        if not opts.typescript:
            return "{{ className, style, onError, onLoad }}"

        props = ["className", "style"]
        if opts.include_error_boundary:
            props.append("onError")
        props.append("onLoad")

        # Add variable props
        for var in opts.variables:
            if var.value_source:
                props.append(f"{var.name}: {var.name}Prop")

        return f"{{ {', '.join(props)} }}: {opts.component_name}Props"

    def _build_event_handlers(self, opts: GenerationOptions) -> str:
        """Build event handler setup code."""
        if not opts.event_handlers:
            return ""

        indent = self._get_indent(1)
        lines = [f"{indent}const handleLoad = useCallback((splineApp: any) => {{"]

        inner_indent = self._get_indent(2)

        # Set up event listeners
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
        lines.append("")

        return "\n".join(lines)

    def _build_variable_setup(self, opts: GenerationOptions) -> str:
        """Build variable initialization code."""
        if not opts.variables:
            return ""

        indent = self._get_indent(1)
        lines = [f"{indent}const initialVariables = {{"]

        inner_indent = self._get_indent(2)
        for var in opts.variables:
            value = var.value_source if var.value_source else repr(var.value)
            lines.append(f"{inner_indent}{var.name}: {value},")

        lines.append(f"{indent}}};")
        lines.append("")

        return "\n".join(lines)

    def _build_websocket_integration(self, opts: GenerationOptions) -> str:
        """Build Mahavishnu WebSocket integration code."""
        if not opts.include_websocket:
            return ""

        indent = self._get_indent(1)
        ws_url = opts.websocket_url or "ws://localhost:8690"

        lines = [
            f"{indent}const splineRef = useRef<any>();",
            f"{indent}const {{ subscribe, isConnected }} = useWebSocket('{ws_url}');",
            "",
            f"{indent}React.useEffect(() => {{",
            f"{indent}  if (!isConnected) return;",
            "",
            f"{indent}  const unsubscribe = subscribe('spline:variables', (data: any) => {{",
            f"{indent}    if (splineRef.current) {{",
            f"{indent}      splineRef.current.setVariables(data);",
            f"{indent}    }}}}",
            f"{indent}  }}}});",
            "",
            f"{indent}  return unsubscribe;",
            f"{indent}}}}}, [isConnected, subscribe]);",
            "",
        ]

        return "\n".join(lines)

    def _build_component_body(
        self,
        scene_url: str,
        opts: GenerationOptions,
    ) -> str:
        """Build the main component body."""
        indent = self._get_indent(1)

        # State for loading and error
        state_lines = [
            f"{indent}const [isLoading, setIsLoading] = useState(true);",
        ]

        if opts.include_error_boundary:
            state_lines.append(f"{indent}const [hasError, setHasError] = useState(false);")

        state_lines.append("")

        # Error boundary check
        error_check = ""
        if opts.include_error_boundary:
            error_check = f"{indent}if (hasError) {{\n"
            error_check += f"{indent}  return (\n"
            error_check += f"{indent}    <div className=\"spline-error\" style={{...style, padding: '20px', textAlign: 'center'}} role=\"alert\">\n"
            error_check += f"{indent}      <p>Failed to load 3D scene. Please try again later.</p>\n"
            error_check += f"{indent}    </div>\n"
            error_check += f"{indent}  );\n"
            error_check += f"{indent}}}\n"

        # Build Spline component
        spline_props = [f'scene="{scene_url}"']
        if opts.event_handlers:
            spline_props.append("onLoad={{handleLoad}}")
        if opts.include_error_boundary:
            spline_props.append("onError={{handleError}}")
        if opts.variables:
            spline_props.append("variables={{initialVariables}}")
        spline_props.append("className={{className}}")
        spline_props.append("style={{style}}")

        spline_component = f"<Spline\n{indent}  {' '.join(spline_props)}\n{indent}/>"

        # Handle error handler
        error_handler = ""
        if opts.include_error_boundary:
            error_handler = f"{indent}const handleError = useCallback((error: Error) => {{\n"
            error_handler += f"{indent}  setHasError(true);\n"
            error_handler += f"{indent}  setIsLoading(false);\n"
            error_handler += f"{indent}  onError?.(error);\n"
            error_handler += f"{indent}  console.error('Spline scene error:', error);\n"
            error_handler += f"{indent}}}, [onError]);\n"

        # Wrap in Suspense if lazy loading
        if opts.lazy_load:
            body = f"{indent}return (\n"
            body += f"{indent}  <Suspense fallback={{<{opts.component_name}Fallback />}}>\n"
            body += f"{indent}    {spline_component}\n"
            body += f"{indent}  </Suspense>\n"
            body += f"{indent});"
        else:
            body = f"{indent}return (\n"
            body += f"{indent}  {spline_component}\n"
            body += f"{indent});"

        return "\n".join(state_lines) + error_handler + error_check + body

    def _generate_fallback(self, opts: GenerationOptions) -> str:
        """Generate loading fallback component."""
        indent = self._get_indent

        lines = [
            f"function {opts.component_name}Fallback() {{",
            f"{indent(1)}return (",
            f"{indent(2)}<div",
            f"{indent(3)}  className=\"spline-loading\"",
            f"{indent(3)}  style={{",
            f"{indent(4)}    display: 'flex',",
            f"{indent(4)}    alignItems: 'center',",
            f"{indent(4)}    justifyContent: 'center',",
            f"{indent(4)}    minHeight: '200px'",
            f"{indent(3)}  }}",
            f"{indent(3)}  aria-busy=\"true\"",
            f"{indent(3)}  aria-label=\"Loading 3D scene\"",
            f"{indent(2)}>",
            f"{indent(3)}<div className=\"spline-spinner\" />",
            f"{indent(2)}</div>",
            f"{indent(1)});",
            "}",
        ]

        return "\n".join(lines)

    def _generate_error_boundary(self, opts: GenerationOptions) -> str:
        """Generate error boundary component."""
        # For simplicity, we handle errors in the main component
        return ""

    def generate_event_handler(
        self,
        handler: EventHandler,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate standalone event handler code."""
        opts = options or self.options
        indent = self._get_indent

        target_filter = ""
        if handler.target_object:
            target_filter = f"if (e.target.name === '{handler.target_object}')"

        lines = [
            f"splineApp.addEventListener('{handler.event_type.value}', (e: any) => {{",
            f"{indent(1)}{target_filter} {{",
            f"{indent(2)}{handler.handler_code}",
            f"{indent(1)}}}",
            "});",
        ]

        return "\n".join(lines)

    def generate_variable_bindings(
        self,
        variables: list[VariableBinding],
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate variable binding code."""
        opts = options or self.options
        indent = self._get_indent

        lines = ["const variables = {"]
        for var in variables:
            value = var.value_source if var.value_source else repr(var.value)
            lines.append(f"{indent(1)}{var.name}: {value},")
        lines.append("};")
        lines.append("")
        lines.append("splineApp.setVariables(variables);")

        return "\n".join(lines)

    def generate_install_instructions(self) -> str:
        """Generate npm install instructions."""
        return "npm install @splinetool/react-spline @splinetool/runtime"

    def generate_usage_example(
        self,
        component_name: str,
        scene_url: str,
    ) -> str:
        """Generate usage example."""
        lines = [
            f"import {{ {component_name} }} from './components/{component_name}';",
            "",
            "// Basic usage",
            f"<{component_name} />",
            "",
            "// With custom styling",
            f"<{component_name} className=\"hero-scene\" style={{ height: '500px' }} />",
            "",
            "// With error handling",
            f"<{component_name}",
            "  onError={{(error) => console.error('Scene failed:', error)}}",
            "  onLoad={{() => console.log('Scene loaded!')}}",
            "/>",
        ]
        return "\n".join(lines)
