"""Base classes for code generators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SplineEventType(str, Enum):
    """Supported Spline event types."""

    MOUSE_DOWN = "mouseDown"
    MOUSE_UP = "mouseUp"
    MOUSE_HOVER = "mouseHover"
    KEY_DOWN = "keyDown"
    KEY_UP = "keyUp"
    START = "start"
    LOOK_AT = "lookAt"
    FOLLOW = "follow"
    SCROLL = "scroll"


class FrameworkType(str, Enum):
    """Supported frameworks for code generation."""

    REACT = "react"
    VANILLA_JS = "vanilla"
    NEXTJS = "nextjs"
    VUE = "vue"


class EventHandler(BaseModel):
    """Event handler configuration."""

    event_type: SplineEventType = Field(..., description="Type of event to handle")
    target_object: str | None = Field(
        default=None, description="Target object name (null for scene-wide)"
    )
    handler_code: str = Field(
        default="console.log('Event triggered');",
        description="JavaScript code to execute",
    )


class VariableBinding(BaseModel):
    """Variable binding configuration."""

    name: str = Field(..., description="Variable name in Spline")
    value: Any = Field(default=None, description="Initial value")
    value_source: str | None = Field(
        default=None,
        description="Source expression (e.g., 'props.myVar')",
    )
    update_on_change: bool = Field(
        default=False,
        description="Whether to update when source changes",
    )


class GenerationOptions(BaseModel):
    """Options for code generation."""

    component_name: str = Field(
        default="SplineScene",
        description="Name of the generated component",
    )
    typescript: bool = Field(default=True, description="Generate TypeScript code")
    lazy_load: bool = Field(default=True, description="Use lazy loading with Suspense")
    ssr_placeholder: bool = Field(
        default=False,
        description="Generate SSR placeholder for Next.js",
    )
    event_handlers: list[EventHandler] = Field(
        default_factory=list,
        description="Event handlers to include",
    )
    variables: list[VariableBinding] = Field(
        default_factory=list,
        description="Variable bindings to include",
    )
    include_error_boundary: bool = Field(
        default=True,
        description="Include error handling",
    )
    include_loading_state: bool = Field(
        default=True,
        description="Include loading state UI",
    )
    include_websocket: bool = Field(
        default=False,
        description="Include Mahavishnu WebSocket integration",
    )
    websocket_url: str | None = Field(
        default="ws://localhost:8690",
        description="WebSocket server URL",
    )
    indent_spaces: int = Field(default=2, description="Indentation spaces")
    semicolons: bool = Field(default=True, description="Use semicolons")


class CodeGenerator(ABC):
    """Abstract base class for code generators."""

    def __init__(self, options: GenerationOptions | None = None) -> None:
        """Initialize the generator with options."""
        self.options = options or GenerationOptions()

    @abstractmethod
    def generate_component(
        self,
        scene_url: str,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate a complete component for the scene.

        Args:
            scene_url: URL to the .splinecode file
            options: Generation options (uses instance options if not provided)

        Returns:
            Generated component code as string
        """
        pass

    @abstractmethod
    def generate_event_handler(
        self,
        handler: EventHandler,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate event handler code.

        Args:
            handler: Event handler configuration
            options: Generation options

        Returns:
            Generated event handler code
        """
        pass

    @abstractmethod
    def generate_variable_bindings(
        self,
        variables: list[VariableBinding],
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate variable binding code.

        Args:
            variables: List of variable bindings
            options: Generation options

        Returns:
            Generated variable binding code
        """
        pass

    def _get_indent(self, level: int = 1) -> str:
        """Get indentation string for the given level."""
        return " " * (self.options.indent_spaces * level)

    def _semicolons(self, code: str) -> str:
        """Add semicolons if configured."""
        if self.options.semicolons:
            return code
        return code.rstrip(";")

    def generate_install_instructions(self) -> str:
        """Generate installation instructions for the framework."""
        return ""

    def generate_usage_example(
        self,
        component_name: str,
        scene_url: str,
    ) -> str:
        """Generate usage example for the component."""
        return f"<{component_name} />"


# Event type documentation
EVENT_TYPE_DOCS: dict[SplineEventType, str] = {
    SplineEventType.MOUSE_DOWN: "Triggered when mouse button is pressed on an object",
    SplineEventType.MOUSE_UP: "Triggered when mouse button is released",
    SplineEventType.MOUSE_HOVER: "Triggered when mouse enters an object",
    SplineEventType.KEY_DOWN: "Triggered when a key is pressed",
    SplineEventType.KEY_UP: "Triggered when a key is released",
    SplineEventType.START: "Triggered when the scene starts",
    SplineEventType.LOOK_AT: "Triggered when camera looks at an object",
    SplineEventType.FOLLOW: "Triggered during follow behavior",
    SplineEventType.SCROLL: "Triggered on scroll events",
}


def get_event_documentation(event_type: SplineEventType) -> str:
    """Get documentation for an event type."""
    return EVENT_TYPE_DOCS.get(event_type, "No documentation available")


__all__ = [
    "SplineEventType",
    "FrameworkType",
    "EventHandler",
    "VariableBinding",
    "GenerationOptions",
    "CodeGenerator",
    "EVENT_TYPE_DOCS",
    "get_event_documentation",
]
