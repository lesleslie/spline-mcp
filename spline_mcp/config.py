"""Configuration for spline-mcp using Oneiric conventions.

See: docs/superpowers/plans/2026-06-26-mcpserver-settings-convention.md

Layered config follows the Oneiric convention:
    defaults -> settings/spline-mcp.yaml -> settings/local.yaml -> env (SPLINE_*)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from oneiric.core.config import OneiricMCPConfig
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


class SplineSettings(OneiricMCPConfig, BaseSettings):
    """Spline MCP server configuration.

    Inherits from OneiricMCPConfig (Bodai convention) and BaseSettings
    (pydantic-settings env loading). Multi-inheritance preserves the
    existing SPLINE_ env_prefix behavior while satisfying the
    ``issubclass(SplineSettings, OneiricMCPConfig)`` convention guard.
    """

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

    @classmethod
    def load(
        cls,
        server_name: str,
        config_path: Path | None = None,
        env_prefix: str | None = None,
    ) -> SplineSettings:
        """Layered config loader mirroring mcp_common.config.MCPBaseSettings.

        Priority (highest to lowest):
            1. Explicit config_path
            2. Environment variables (SPLINE_*)
            3. settings/local.yaml (gitignored)
            4. settings/{server_name}.yaml
            5. Field defaults

        Args:
            server_name: Server identifier (e.g., "spline-mcp").
            config_path: Optional explicit config file path.
            env_prefix: Environment variable prefix (default "SPLINE").

        Returns:
            Loaded SplineSettings instance with all layers applied.
        """
        data: dict[str, Any] = {"server_name": server_name}

        if env_prefix is None:
            env_prefix = "SPLINE"

        # YAML layers
        server_yaml = Path("settings") / f"{server_name}.yaml"
        if server_yaml.exists():
            with server_yaml.open() as f:
                import yaml

                yaml_data = yaml.safe_load(f)
                if isinstance(yaml_data, dict):
                    data.update(yaml_data)

        local_yaml = Path("settings") / "local.yaml"
        if local_yaml.exists():
            with local_yaml.open() as f:
                import yaml

                local_data = yaml.safe_load(f)
                if isinstance(local_data, dict):
                    data.update(local_data)

        # Env layer
        for field_name in cls.model_fields:
            env_var = f"{env_prefix}_{field_name.upper()}"
            if env_var in os.environ:
                env_value: str | Path | None = os.environ[env_var]
                field_type = cls.model_fields[field_name].annotation
                from typing import get_args

                field_args = get_args(field_type)
                if field_type is Path or (field_args and Path in field_args):
                    env_value = Path(env_value) if env_value else None
                data[field_name] = env_value

        # Explicit config layer
        if config_path is not None and config_path.exists():
            with config_path.open() as f:
                import yaml

                explicit_data = yaml.safe_load(f)
                if isinstance(explicit_data, dict):
                    data.update(explicit_data)

        return cls.model_validate(data)


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
