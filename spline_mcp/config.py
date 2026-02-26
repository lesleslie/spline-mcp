"""Configuration for spline-mcp using Oneiric patterns."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Oneiric logging imports
try:
    from oneiric.core.logging import LoggingConfig, configure_logging, get_logger

    ONEIRIC_LOGGING_AVAILABLE = True
except ImportError:
    ONEIRIC_LOGGING_AVAILABLE = False
    import logging

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    def configure_logging(*args: Any, **kwargs: Any) -> None:
        logging.basicConfig(level=logging.INFO)


class SplineSettings(BaseSettings):
    """Spline MCP server configuration."""

    model_config = SettingsConfigDict(
        env_prefix="SPLINE_",
        env_file=(".env",),
        extra="ignore",
        case_sensitive=False,
    )

    # Server identification
    server_name: str = Field(
        default="spline-mcp",
        description="Server name for identification",
    )
    server_description: str = Field(
        default="MCP server for Spline.design code generation and asset management",
        description="Server description",
    )

    # Code generation defaults
    default_framework: Literal["react", "vanilla", "nextjs"] = Field(
        default="react",
        description="Default framework for code generation",
    )
    typescript: bool = Field(
        default=True,
        description="Generate TypeScript code by default",
    )
    lazy_load: bool = Field(
        default=True,
        description="Use lazy loading with Suspense by default",
    )
    ssr_placeholder: bool = Field(
        default=False,
        description="Generate SSR placeholder for Next.js by default",
    )

    # Code style
    indent_spaces: int = Field(
        default=2,
        ge=2,
        le=8,
        description="Indentation spaces for generated code",
    )
    semicolons: bool = Field(
        default=True,
        description="Use semicolons in generated JavaScript",
    )

    # Asset management
    cache_dir: Path = Field(
        default=Path("~/.spline-mcp/cache").expanduser(),
        description="Directory for cached .splinecode files",
    )
    max_cache_size_mb: int = Field(
        default=500,
        ge=100,
        le=5000,
        description="Maximum cache size in megabytes",
    )
    auto_validate: bool = Field(
        default=True,
        description="Automatically validate downloaded scenes",
    )

    # WebSocket integration (Mahavishnu)
    websocket_enabled: bool = Field(
        default=True,
        description="Enable WebSocket integration with Mahavishnu",
    )
    websocket_url: str = Field(
        default="ws://localhost:8690",
        description="Mahavishnu WebSocket server URL",
    )
    websocket_auto_reconnect: bool = Field(
        default=True,
        description="Automatically reconnect on disconnect",
    )

    # n8n integration
    n8n_enabled: bool = Field(
        default=True,
        description="Enable n8n integration",
    )
    n8n_url: str = Field(
        default="http://localhost:3044",
        description="n8n server URL",
    )
    n8n_api_key: str | None = Field(
        default=None,
        description="n8n API key",
    )

    # HTTP transport
    enable_http_transport: bool = Field(
        default=False,
        description="Enable HTTP transport",
    )
    http_host: str = Field(
        default="127.0.0.1",
        description="HTTP server host",
    )
    http_port: int = Field(
        default=3048,
        ge=1024,
        le=65535,
        description="HTTP server port",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_json: bool = Field(
        default=True,
        description="Use JSON logging format",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid}")
        return v.upper()

    @field_validator("cache_dir", mode="before")
    @classmethod
    def expand_cache_dir(cls, v: str | Path) -> Path:
        """Expand cache directory path."""
        return Path(v).expanduser()


@lru_cache
def get_settings() -> SplineSettings:
    """Get cached settings instance."""
    return SplineSettings()


def setup_logging(settings: SplineSettings | None = None) -> None:
    """Configure logging using Oneiric patterns."""
    if settings is None:
        settings = get_settings()

    if ONEIRIC_LOGGING_AVAILABLE:
        config = LoggingConfig(
            level=settings.log_level,
            emit_json=settings.log_json,
            service_name="spline-mcp",
        )
        configure_logging(config)
    else:
        import logging

        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


def get_logger_instance(name: str = "spline-mcp") -> Any:
    """Get a structured logger instance."""
    if ONEIRIC_LOGGING_AVAILABLE:
        return get_logger(name)
    import logging

    return logging.getLogger(name)


__all__ = [
    "SplineSettings",
    "get_settings",
    "setup_logging",
    "get_logger_instance",
    "ONEIRIC_LOGGING_AVAILABLE",
]
