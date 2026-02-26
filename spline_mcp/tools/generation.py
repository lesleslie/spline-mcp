"""Code generation MCP tools."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp import FastMCP

from spline_mcp.config import get_logger_instance, get_settings
from spline_mcp.generators.base import (
    EventHandler,
    FrameworkType,
    GenerationOptions,
    SplineEventType,
    VariableBinding,
)
from spline_mcp.generators.nextjs import NextJSGenerator
from spline_mcp.generators.react import ReactGenerator
from spline_mcp.generators.vanilla import VanillaJSGenerator

logger = get_logger_instance("spline-mcp.tools.generation")


def register_generation_tools(app: FastMCP) -> None:
    """Register code generation tools."""

    @app.tool()
    async def generate_react_component(
        scene_url: str,
        component_name: str = "SplineScene",
        typescript: bool = True,
        lazy_load: bool = True,
        include_websocket: bool = False,
        websocket_url: str = "ws://localhost:8690",
    ) -> dict[str, Any]:
        """Generate a React component for a Spline scene.

        Args:
            scene_url: URL to the .splinecode file or scene ID
            component_name: Name of the generated component
            typescript: Generate TypeScript code
            lazy_load: Use lazy loading with Suspense
            include_websocket: Include Mahavishnu WebSocket integration
            websocket_url: WebSocket server URL

        Returns:
            Generated component code and metadata
        """
        settings = get_settings()

        # Normalize URL
        if not scene_url.startswith("http"):
            scene_url = f"https://prod.spline.design/{scene_url}/scene.splinecode"

        options = GenerationOptions(
            component_name=component_name,
            typescript=typescript,
            lazy_load=lazy_load,
            include_websocket=include_websocket,
            websocket_url=websocket_url,
            indent_spaces=settings.indent_spaces,
            semicolons=settings.semicolons,
        )

        generator = ReactGenerator(options)
        code = generator.generate_component(scene_url, options)

        logger.info(
            "Generated React component",
            component_name=component_name,
            scene_url=scene_url,
            typescript=typescript,
        )

        return {
            "code": code,
            "component_name": component_name,
            "framework": "react",
            "typescript": typescript,
            "install_command": generator.generate_install_instructions(),
            "usage_example": generator.generate_usage_example(component_name, scene_url),
        }

    @app.tool()
    async def generate_vanilla_js(
        scene_url: str,
        include_websocket: bool = False,
        websocket_url: str = "ws://localhost:8690",
    ) -> dict[str, Any]:
        """Generate vanilla JavaScript/HTML for a Spline scene.

        Args:
            scene_url: URL to the .splinecode file or scene ID
            include_websocket: Include Mahavishnu WebSocket integration
            websocket_url: WebSocket server URL

        Returns:
            Generated HTML/JS code and metadata
        """
        settings = get_settings()

        # Normalize URL
        if not scene_url.startswith("http"):
            scene_url = f"https://prod.spline.design/{scene_url}/scene.splinecode"

        options = GenerationOptions(
            include_websocket=include_websocket,
            websocket_url=websocket_url,
            indent_spaces=settings.indent_spaces,
            semicolons=settings.semicolons,
        )

        generator = VanillaJSGenerator(options)
        code = generator.generate_component(scene_url, options)

        logger.info(
            "Generated vanilla JS integration",
            scene_url=scene_url,
            include_websocket=include_websocket,
        )

        return {
            "code": code,
            "framework": "vanilla",
            "install_instructions": generator.generate_install_instructions(),
            "usage_example": generator.generate_usage_example("SplineScene", scene_url),
        }

    @app.tool()
    async def generate_nextjs_component(
        scene_url: str,
        component_name: str = "SplineScene",
        typescript: bool = True,
        ssr_placeholder: bool = True,
        include_websocket: bool = False,
        websocket_url: str = "ws://localhost:8690",
    ) -> dict[str, Any]:
        """Generate a Next.js component with SSR support.

        Args:
            scene_url: URL to the .splinecode file or scene ID
            component_name: Name of the generated component
            typescript: Generate TypeScript code
            ssr_placeholder: Generate SSR placeholder
            include_websocket: Include Mahavishnu WebSocket integration
            websocket_url: WebSocket server URL

        Returns:
            Generated component code and metadata
        """
        settings = get_settings()

        # Normalize URL
        if not scene_url.startswith("http"):
            scene_url = f"https://prod.spline.design/{scene_url}/scene.splinecode"

        options = GenerationOptions(
            component_name=component_name,
            typescript=typescript,
            ssr_placeholder=ssr_placeholder,
            include_websocket=include_websocket,
            websocket_url=websocket_url,
            indent_spaces=settings.indent_spaces,
            semicolons=settings.semicolons,
        )

        generator = NextJSGenerator(options)
        code = generator.generate_component(scene_url, options)

        logger.info(
            "Generated Next.js component",
            component_name=component_name,
            scene_url=scene_url,
            ssr_placeholder=ssr_placeholder,
        )

        return {
            "code": code,
            "component_name": component_name,
            "framework": "nextjs",
            "typescript": typescript,
            "install_command": generator.generate_install_instructions(),
            "usage_example": generator.generate_usage_example(component_name, scene_url),
        }

    @app.tool()
    async def generate_event_handler(
        event_type: str,
        handler_code: str = "console.log('Event triggered');",
        target_object: str | None = None,
        framework: Literal["react", "vanilla", "nextjs"] = "react",
    ) -> dict[str, Any]:
        """Generate event handler code for Spline events.

        Args:
            event_type: Type of event (mouseDown, mouseUp, mouseHover, keyDown, etc.)
            handler_code: JavaScript code to execute
            target_object: Target object name (optional)
            framework: Target framework

        Returns:
            Generated event handler code
        """
        try:
            event = SplineEventType(event_type)
        except ValueError:
            valid = [e.value for e in SplineEventType]
            return {
                "error": f"Invalid event type: {event_type}",
                "valid_types": valid,
            }

        handler = EventHandler(
            event_type=event,
            handler_code=handler_code,
            target_object=target_object,
        )

        if framework == "react":
            generator = ReactGenerator()
        elif framework == "nextjs":
            generator = NextJSGenerator()
        else:
            generator = VanillaJSGenerator()

        code = generator.generate_event_handler(handler)

        logger.info(
            "Generated event handler",
            event_type=event_type,
            target_object=target_object,
            framework=framework,
        )

        return {
            "code": code,
            "event_type": event_type,
            "framework": framework,
        }

    @app.tool()
    async def generate_variable_binding(
        variables: dict[str, Any],
        framework: Literal["react", "vanilla", "nextjs"] = "react",
    ) -> dict[str, Any]:
        """Generate variable binding code for Spline runtime.

        Args:
            variables: Dictionary of variable names to values
            framework: Target framework

        Returns:
            Generated variable binding code
        """
        bindings = [
            VariableBinding(name=name, value=value)
            for name, value in variables.items()
        ]

        if framework == "react":
            generator = ReactGenerator()
        elif framework == "nextjs":
            generator = NextJSGenerator()
        else:
            generator = VanillaJSGenerator()

        code = generator.generate_variable_bindings(bindings)

        logger.info(
            "Generated variable bindings",
            variable_count=len(variables),
            framework=framework,
        )

        return {
            "code": code,
            "variables": variables,
            "framework": framework,
        }

    @app.tool()
    async def generate_full_integration(
        scene_url: str,
        framework: Literal["react", "vanilla", "nextjs"] = "react",
        component_name: str = "SplineScene",
        event_handlers: list[dict[str, Any]] | None = None,
        variables: dict[str, Any] | None = None,
        include_websocket: bool = False,
    ) -> dict[str, Any]:
        """Generate complete integration code with all features.

        Args:
            scene_url: URL to the .splinecode file or scene ID
            framework: Target framework
            component_name: Name of the generated component
            event_handlers: List of event handler configs
            variables: Dictionary of variable bindings
            include_websocket: Include Mahavishnu WebSocket integration

        Returns:
            Complete integration code package
        """
        settings = get_settings()

        # Normalize URL
        if not scene_url.startswith("http"):
            scene_url = f"https://prod.spline.design/{scene_url}/scene.splinecode"

        # Build options
        handlers = []
        if event_handlers:
            for h in event_handlers:
                try:
                    handlers.append(EventHandler(
                        event_type=SplineEventType(h.get("event_type", "mouseDown")),
                        handler_code=h.get("handler_code", "console.log('Event');"),
                        target_object=h.get("target_object"),
                    ))
                except (ValueError, KeyError):
                    continue

        bindings = []
        if variables:
            bindings = [
                VariableBinding(name=name, value=value)
                for name, value in variables.items()
            ]

        options = GenerationOptions(
            component_name=component_name,
            typescript=settings.typescript,
            lazy_load=settings.lazy_load,
            ssr_placeholder=settings.ssr_placeholder,
            event_handlers=handlers,
            variables=bindings,
            include_websocket=include_websocket,
            websocket_url=settings.websocket_url,
            indent_spaces=settings.indent_spaces,
            semicolons=settings.semicolons,
        )

        # Select generator
        if framework == "react":
            generator = ReactGenerator(options)
        elif framework == "nextjs":
            generator = NextJSGenerator(options)
        else:
            generator = VanillaJSGenerator(options)

        code = generator.generate_component(scene_url, options)

        logger.info(
            "Generated full integration",
            framework=framework,
            component_name=component_name,
            event_handlers=len(handlers),
            variables=len(bindings),
        )

        return {
            "code": code,
            "component_name": component_name,
            "framework": framework,
            "install_command": generator.generate_install_instructions(),
            "usage_example": generator.generate_usage_example(component_name, scene_url),
            "features": {
                "event_handlers": len(handlers),
                "variables": len(bindings),
                "websocket": include_websocket,
            },
        }


__all__ = ["register_generation_tools"]
