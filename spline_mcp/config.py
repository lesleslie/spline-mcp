"""Configuration for spline-mcp using Oneiric patterns."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

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
        default="MCP server for Spline.design 3D scene orchestration",
        description="Server description",
    )

    # Spline API configuration
    api_key: str | None = Field(
        default=None,
        description="Spline API key for authentication",
    )
    api_base_url: str = Field(
        default="https://api.spline.design/v1",
        description="Spline API base URL",
    )
    api_timeout: float = Field(
        default=30.0,
        ge=5.0,
        le=120.0,
        description="API request timeout in seconds",
    )

    # Scene management
    default_scene_id: str | None = Field(
        default=None,
        description="Default scene ID for operations",
    )
    auto_save: bool = Field(
        default=True,
        description="Auto-save scene after modifications",
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
