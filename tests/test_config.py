"""Unit tests for configuration module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spline_mcp.config import (
    SplineSettings,
    get_logger_instance,
    get_settings,
    setup_logging,
)


class TestSplineSettings:
    """Tests for SplineSettings."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        settings = SplineSettings()

        # Check defaults - use actual values from config
        assert settings.server_name == "spline-mcp"
        assert settings.default_framework == "react"
        assert settings.typescript is True
        assert settings.lazy_load is True
        # ssr_placeholder default is False
        assert settings.ssr_placeholder is False
        assert settings.indent_spaces == 2
        assert settings.semicolons is True

    def test_websocket_defaults(self) -> None:
        """Test WebSocket default settings."""
        settings = SplineSettings()

        assert settings.websocket_enabled is True
        assert settings.websocket_url == "ws://localhost:8690"
        assert settings.websocket_auto_reconnect is True

    def test_n8n_defaults(self) -> None:
        """Test n8n default settings."""
        settings = SplineSettings()

        assert settings.n8n_enabled is True
        assert settings.n8n_url == "http://localhost:3044"

    def test_cache_defaults(self) -> None:
        """Test cache default settings."""
        settings = SplineSettings()

        assert settings.cache_dir is not None
        assert settings.max_cache_size_mb == 500

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        settings = SplineSettings(
            server_name="custom-server",
            default_framework="vanilla",
            typescript=False,
            indent_spaces=4,
        )

        assert settings.server_name == "custom-server"
        assert settings.default_framework == "vanilla"
        assert settings.typescript is False
        assert settings.indent_spaces == 4

    def test_cache_dir_expanded(self) -> None:
        """Test cache directory path expansion."""
        settings = SplineSettings(
            cache_dir=Path("~/custom/cache"),
        )

        # Path should be expanded
        assert "~" not in str(settings.cache_dir)

    def test_environment_variable_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable override."""
        # Clear the cache first
        get_settings.cache_clear()

        monkeypatch.setenv("SPLINE_SERVER_NAME", "env-server")
        monkeypatch.setenv("SPLINE_TYPESCRIPT", "false")
        monkeypatch.setenv("SPLINE_INDENT_SPACES", "4")

        # Need to create a new instance to pick up env vars
        settings = SplineSettings()
        assert settings.server_name == "env-server"
        assert settings.typescript is False
        assert settings.indent_spaces == 4

    def test_model_config(self) -> None:
        """Test model configuration."""
        settings = SplineSettings()

        # Check that settings can be created
        assert settings.model_config is not None


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_same_instance(self) -> None:
        """Test that get_settings returns singleton."""
        # Clear any cached instance
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_returns_splinesettings(self) -> None:
        """Test that get_settings returns SplineSettings."""
        get_settings.cache_clear()

        settings = get_settings()

        assert isinstance(settings, SplineSettings)


class TestGetLoggerInstance:
    """Tests for get_logger_instance function."""

    def test_returns_logger(self) -> None:
        """Test that it returns a logger."""
        logger = get_logger_instance("test-module")
        assert logger is not None

    def test_different_names(self) -> None:
        """Test that different names can be used."""
        logger1 = get_logger_instance("module1")
        logger2 = get_logger_instance("module2")

        # Both should return valid logger objects
        assert logger1 is not None
        assert logger2 is not None
        # They are different instances (structlog creates new proxies)
        assert logger1 is not logger2


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_with_settings(self) -> None:
        """Test setup_logging with custom settings."""
        settings = MagicMock()
        settings.log_level = "INFO"
        settings.log_json = False

        # Should not raise
        setup_logging(settings)

    def test_setup_logging_default_level(self) -> None:
        """Test setup_logging with default level."""
        settings = MagicMock()
        settings.log_level = "INFO"
        settings.log_json = False

        # Should not raise
        setup_logging(settings)

    def test_setup_logging_none_uses_get_settings(self) -> None:
        """Test setup_logging with None uses get_settings."""
        # Should not raise
        setup_logging(None)


class TestSplineSettingsValidation:
    """Tests for SplineSettings validation."""

    def test_invalid_log_level(self) -> None:
        """Test invalid log level raises error."""
        with pytest.raises(ValueError, match="Invalid log level"):
            SplineSettings(log_level="INVALID")

    def test_valid_log_levels(self) -> None:
        """Test all valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = SplineSettings(log_level=level)
            assert settings.log_level == level

    def test_invalid_framework(self) -> None:
        """Test invalid framework raises error."""
        with pytest.raises(ValueError):
            SplineSettings(default_framework="invalid")

    def test_valid_frameworks(self) -> None:
        """Test all valid frameworks."""
        for framework in ["react", "vanilla", "nextjs"]:
            settings = SplineSettings(default_framework=framework)
            assert settings.default_framework == framework

    def test_indent_spaces_range(self) -> None:
        """Test indent spaces must be in valid range."""
        # Valid range
        for spaces in [2, 4, 8]:
            settings = SplineSettings(indent_spaces=spaces)
            assert settings.indent_spaces == spaces

        # Invalid - too small
        with pytest.raises(ValueError):
            SplineSettings(indent_spaces=1)

        # Invalid - too large
        with pytest.raises(ValueError):
            SplineSettings(indent_spaces=10)
