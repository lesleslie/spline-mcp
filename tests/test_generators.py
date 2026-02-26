"""Unit tests for code generators."""

from __future__ import annotations

import pytest

from spline_mcp.generators.base import (
    CodeGenerator,
    EventHandler,
    GenerationOptions,
    SplineEventType,
    VariableBinding,
)
from spline_mcp.generators.react import ReactGenerator
from spline_mcp.generators.vanilla import VanillaJSGenerator
from spline_mcp.generators.nextjs import NextJSGenerator


class TestGenerationOptions:
    """Tests for GenerationOptions."""

    def test_defaults(self) -> None:
        """Test default options."""
        opts = GenerationOptions()
        assert opts.component_name == "SplineScene"
        assert opts.typescript is True
        assert opts.lazy_load is True
        assert opts.include_websocket is False

    def test_custom_options(self) -> None:
        """Test custom options."""
        opts = GenerationOptions(
            component_name="HeroScene",
            typescript=False,
            lazy_load=False,
            include_websocket=True,
            websocket_url="ws://custom:9999",
        )
        assert opts.component_name == "HeroScene"
        assert opts.typescript is False
        assert opts.lazy_load is False
        assert opts.include_websocket is True
        assert opts.websocket_url == "ws://custom:9999"


class TestEventHandler:
    """Tests for EventHandler."""

    def test_basic_handler(self) -> None:
        """Test basic event handler."""
        handler = EventHandler(
            event_type=SplineEventType.MOUSE_DOWN,
            handler_code="console.log('clicked')",
        )
        assert handler.event_type == SplineEventType.MOUSE_DOWN
        assert handler.target_object is None
        assert "clicked" in handler.handler_code

    def test_targeted_handler(self) -> None:
        """Test targeted event handler."""
        handler = EventHandler(
            event_type=SplineEventType.MOUSE_HOVER,
            target_object="Button",
            handler_code="console.log('hover')",
        )
        assert handler.target_object == "Button"
        assert handler.event_type == SplineEventType.MOUSE_HOVER


class TestVariableBinding:
    """Tests for VariableBinding."""

    def test_static_value(self) -> None:
        """Test static value binding."""
        binding = VariableBinding(name="color", value="#ff0000")
        assert binding.name == "color"
        assert binding.value == "#ff0000"
        assert binding.value_source is None

    def test_dynamic_source(self) -> None:
        """Test dynamic source binding."""
        binding = VariableBinding(
            name="speed",
            value=1.0,
            value_source="props.speed",
            update_on_change=True,
        )
        assert binding.value_source == "props.speed"
        assert binding.update_on_change is True


class TestReactGenerator:
    """Tests for ReactGenerator."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.scene_url = "https://prod.spline.design/test/scene.splinecode"
        self.generator = ReactGenerator()

    def test_basic_component(self) -> None:
        """Test basic React component generation."""
        code = self.generator.generate_component(self.scene_url)

        assert "import" in code
        assert "Spline" in code
        assert "SplineScene" in code
        assert self.scene_url in code

    def test_typescript_component(self) -> None:
        """Test TypeScript component generation."""
        opts = GenerationOptions(typescript=True)
        code = self.generator.generate_component(self.scene_url, opts)

        assert "interface" in code
        assert "Props" in code
        assert ": " in code  # TypeScript type annotations

    def test_javascript_component(self) -> None:
        """Test JavaScript component generation."""
        opts = GenerationOptions(typescript=False)
        code = self.generator.generate_component(self.scene_url, opts)

        # Should not have TypeScript interfaces
        assert "interface" not in code or "Props" not in code

    def test_with_websocket(self) -> None:
        """Test component with WebSocket integration."""
        opts = GenerationOptions(
            include_websocket=True,
            websocket_url="ws://localhost:8690",
        )
        code = self.generator.generate_component(self.scene_url, opts)

        assert "useWebSocket" in code
        assert "ws://localhost:8690" in code
        assert "subscribe" in code

    def test_with_event_handlers(self) -> None:
        """Test component with event handlers."""
        opts = GenerationOptions(
            event_handlers=[
                EventHandler(
                    event_type=SplineEventType.MOUSE_DOWN,
                    handler_code="console.log('click')",
                ),
            ]
        )
        code = self.generator.generate_component(self.scene_url, opts)

        assert "addEventListener" in code
        assert "mouseDown" in code

    def test_with_variables(self) -> None:
        """Test component with variable bindings."""
        opts = GenerationOptions(
            variables=[
                VariableBinding(name="color", value="#ff0000"),
            ]
        )
        code = self.generator.generate_component(self.scene_url, opts)

        assert "variables" in code.lower()
        assert "setVariables" in code or "initialVariables" in code

    def test_lazy_loading(self) -> None:
        """Test lazy loading with Suspense."""
        opts = GenerationOptions(lazy_load=True)
        code = self.generator.generate_component(self.scene_url, opts)

        assert "Suspense" in code
        assert "Fallback" in code

    def test_no_lazy_loading(self) -> None:
        """Test without lazy loading."""
        opts = GenerationOptions(lazy_load=False)
        code = self.generator.generate_component(self.scene_url, opts)

        # Should still have the component but without Suspense
        assert "Spline" in code

    def test_install_instructions(self) -> None:
        """Test install instructions generation."""
        instructions = self.generator.generate_install_instructions()

        assert "@splinetool/react-spline" in instructions
        assert "@splinetool/runtime" in instructions

    def test_usage_example(self) -> None:
        """Test usage example generation."""
        example = self.generator.generate_usage_example("HeroScene", self.scene_url)

        assert "HeroScene" in example
        assert "import" in example


class TestVanillaJSGenerator:
    """Tests for VanillaJSGenerator."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.scene_url = "https://prod.spline.design/test/scene.splinecode"
        self.generator = VanillaJSGenerator()

    def test_html_generation(self) -> None:
        """Test HTML generation."""
        code = self.generator.generate_component(self.scene_url)

        assert "<!DOCTYPE html>" in code
        assert "<html" in code
        assert "<canvas" in code or "canvas" in code
        assert self.scene_url in code

    def test_with_websocket(self) -> None:
        """Test vanilla JS with WebSocket."""
        opts = GenerationOptions(
            include_websocket=True,
            websocket_url="ws://localhost:8690",
        )
        code = self.generator.generate_component(self.scene_url, opts)

        assert "WebSocket" in code
        assert "ws://localhost:8690" in code
        # Should have soft failover
        assert "catch" in code or "onerror" in code

    def test_with_variables(self) -> None:
        """Test vanilla JS with variables."""
        opts = GenerationOptions(
            variables=[
                VariableBinding(name="speed", value=2.5),
            ]
        )
        code = self.generator.generate_component(self.scene_url, opts)

        assert "variables" in code.lower()
        assert "2.5" in code

    def test_install_instructions(self) -> None:
        """Test install instructions."""
        instructions = self.generator.generate_install_instructions()

        assert "CDN" in instructions or "npm" in instructions


class TestNextJSGenerator:
    """Tests for NextJSGenerator."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.scene_url = "https://prod.spline.design/test/scene.splinecode"
        self.generator = NextJSGenerator()

    def test_component_generation(self) -> None:
        """Test Next.js component generation."""
        code = self.generator.generate_component(self.scene_url)

        assert "use client" in code
        assert "dynamic" in code
        assert "ssr: false" in code

    def test_ssr_placeholder(self) -> None:
        """Test SSR placeholder generation."""
        opts = GenerationOptions(ssr_placeholder=True)
        code = self.generator.generate_component(self.scene_url, opts)

        assert "Placeholder" in code or "placeholder" in code

    def test_with_websocket(self) -> None:
        """Test Next.js with WebSocket."""
        opts = GenerationOptions(
            include_websocket=True,
            websocket_url="ws://localhost:8690",
        )
        code = self.generator.generate_component(self.scene_url, opts)

        assert "useWebSocket" in code or "WebSocket" in code

    def test_install_instructions(self) -> None:
        """Test install instructions."""
        instructions = self.generator.generate_install_instructions()

        assert "next" in instructions.lower()


class TestEventHandlers:
    """Tests for event handler generation."""

    def test_react_event_handler(self) -> None:
        """Test React event handler generation."""
        generator = ReactGenerator()
        handler = EventHandler(
            event_type=SplineEventType.MOUSE_DOWN,
            target_object="Cube",
            handler_code="console.log('clicked')",
        )

        code = generator.generate_event_handler(handler)

        assert "addEventListener" in code
        assert "mouseDown" in code
        assert "Cube" in code
        assert "clicked" in code

    def test_vanilla_event_handler(self) -> None:
        """Test vanilla JS event handler generation."""
        generator = VanillaJSGenerator()
        handler = EventHandler(
            event_type=SplineEventType.MOUSE_HOVER,
            handler_code="e.target.emitEvent('mouseDown')",
        )

        code = generator.generate_event_handler(handler)

        assert "addEventListener" in code
        assert "mouseHover" in code


class TestVariableBindings:
    """Tests for variable binding generation."""

    def test_react_variables(self) -> None:
        """Test React variable binding generation."""
        generator = ReactGenerator()
        variables = [
            VariableBinding(name="color", value="#ff0000"),
            VariableBinding(name="speed", value=2.5),
        ]

        code = generator.generate_variable_bindings(variables)

        assert "variables" in code
        assert "color" in code
        assert "speed" in code
        assert "setVariables" in code

    def test_vanilla_variables(self) -> None:
        """Test vanilla JS variable binding generation."""
        generator = VanillaJSGenerator()
        variables = [
            VariableBinding(name="visible", value=True),
        ]

        code = generator.generate_variable_bindings(variables)

        assert "variables" in code
        assert "visible" in code


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_event_handlers(self) -> None:
        """Test with empty event handlers list."""
        generator = ReactGenerator()
        opts = GenerationOptions(event_handlers=[])
        code = generator.generate_component(
            "https://prod.spline.design/test/scene.splinecode", opts
        )

        # Should still generate valid component
        assert "Spline" in code

    def test_empty_variables(self) -> None:
        """Test with empty variables list."""
        generator = ReactGenerator()
        opts = GenerationOptions(variables=[])
        code = generator.generate_component(
            "https://prod.spline.design/test/scene.splinecode", opts
        )

        # Should still generate valid component
        assert "Spline" in code

    def test_special_characters_in_name(self) -> None:
        """Test component name with special characters."""
        generator = ReactGenerator()
        opts = GenerationOptions(component_name="Hero3DScene")
        code = generator.generate_component(
            "https://prod.spline.design/test/scene.splinecode", opts
        )

        assert "Hero3DScene" in code

    def test_long_scene_url(self) -> None:
        """Test with long scene URL."""
        generator = ReactGenerator()
        long_url = "https://prod.spline.design/very-long-scene-id-with-many-characters-123456789/scene.splinecode"
        code = generator.generate_component(long_url)

        assert long_url in code
