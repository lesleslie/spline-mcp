"""Unit tests for server module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from spline_mcp.server import APP_NAME, APP_VERSION, create_app, get_app


class TestServerCreation:
    """Tests for server creation."""

    def test_app_name(self) -> None:
        """Test app name constant."""
        assert APP_NAME == "spline-mcp"

    def test_app_version(self) -> None:
        """Test app version constant."""
        assert isinstance(APP_VERSION, str)
        assert len(APP_VERSION.split(".")) >= 2

    def test_create_app(self) -> None:
        """Test app creation."""
        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app = create_app()

        assert app is not None
        assert app.name == APP_NAME

    def test_create_app_registers_tools(self) -> None:
        """Test that create_app registers all tools."""
        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                with patch("spline_mcp.server.register_generation_tools") as mock_gen:
                    with patch("spline_mcp.server.register_asset_tools") as mock_asset:
                        with patch("spline_mcp.server.register_helper_tools") as mock_helper:
                            with patch("spline_mcp.server.register_integration_tools") as mock_int:
                                with patch("spline_mcp.server.register_docs_tools") as mock_docs:
                                    app = create_app()

                                    mock_gen.assert_called_once()
                                    mock_asset.assert_called_once()
                                    mock_helper.assert_called_once()
                                    mock_int.assert_called_once()
                                    mock_docs.assert_called_once()


class TestGetApp:
    """Tests for get_app singleton."""

    def test_get_app_returns_same_instance(self) -> None:
        """Test that get_app returns singleton."""
        import spline_mcp.server as server_module

        # Reset singleton
        server_module._app = None

        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app1 = get_app()
                app2 = get_app()

        assert app1 is app2

    def test_get_app_creates_on_first_call(self) -> None:
        """Test that get_app creates app on first call."""
        import spline_mcp.server as server_module

        # Reset singleton
        server_module._app = None

        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app = get_app()

        assert app is not None
        assert server_module._app is app


class TestDynamicAttributeAccess:
    """Tests for __getattr__ dynamic access."""

    def test_app_attribute(self) -> None:
        """Test accessing app attribute."""
        import spline_mcp.server as server_module

        server_module._app = None

        with patch("spline_mcp.server.get_settings") as mock_settings:
            settings = MagicMock()
            settings.default_framework = "react"
            settings.websocket_enabled = True
            settings.n8n_enabled = True
            mock_settings.return_value = settings

            with patch("spline_mcp.server.setup_logging"):
                app = server_module.app

        assert app is not None

    def test_http_app_attribute(self) -> None:
        """Test accessing http_app attribute."""
        import spline_mcp.server as server_module

        server_module._app = None

        mock_app = MagicMock()
        mock_app.http_app = MagicMock()

        with patch("spline_mcp.server.get_app", return_value=mock_app):
            http_app = server_module.http_app

        assert http_app is not None

    def test_invalid_attribute(self) -> None:
        """Test accessing invalid attribute raises."""
        import spline_mcp.server as server_module

        with pytest.raises(AttributeError, match="has no attribute"):
            _ = server_module.nonexistent_attr
