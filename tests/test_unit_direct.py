# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Unit tests for direct service keywords."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from RADKit import RADKit
from RADKit._base import RADKitLibraryError


@pytest.fixture
def library() -> RADKit:
    """Create a RADKit library instance."""
    with patch("RADKit._base.BuiltIn"):
        lib = RADKit()
        lib._client = MagicMock()
        return lib


class TestRadkitServiceDirect:
    """Tests for RADKit service direct keyword."""

    def test_connect_direct_with_env_password(self, library: RADKit) -> None:
        """Test direct connection with password from env var."""
        mock_service = MagicMock()
        mock_service.name = "test-service"
        library.client.service_direct.return_value.wait.return_value = mock_service

        with patch.dict(os.environ, {"MY_PASSWORD": "secret123"}):
            result = library.radkit_service_direct(
                username="admin",
                password="MY_PASSWORD",
                host="10.0.0.1",
            )

        library.client.service_direct.assert_called_once_with(
            username="admin",
            password="secret123",
            host="10.0.0.1",
            port=8181,
            sha256_fingerprint=None,
        )
        assert result == mock_service
        assert library.current_service == mock_service
        assert library.direct_services["10.0.0.1-8181"] == mock_service
        assert library.direct_services_users["10.0.0.1-8181"] == "admin"

    def test_connect_direct_with_custom_port(self, library: RADKit) -> None:
        """Test direct connection with custom port."""
        mock_service = MagicMock()
        library.client.service_direct.return_value.wait.return_value = mock_service

        with patch.dict(os.environ, {"PW": "pass"}):
            library.radkit_service_direct(
                username="admin",
                password="PW",
                host="10.0.0.1",
                port=9090,
            )

        assert library.direct_services["10.0.0.1-9090"] == mock_service

    def test_connect_direct_with_fingerprint(self, library: RADKit) -> None:
        """Test direct connection with SHA256 fingerprint."""
        mock_service = MagicMock()
        library.client.service_direct.return_value.wait.return_value = mock_service

        with patch.dict(os.environ, {"PW": "pass"}):
            library.radkit_service_direct(
                username="admin",
                password="PW",
                host="10.0.0.1",
                sha256_fingerprint="AA:BB:CC",
            )

        library.client.service_direct.assert_called_once_with(
            username="admin",
            password="pass",
            host="10.0.0.1",
            port=8181,
            sha256_fingerprint="AA:BB:CC",
        )

    def test_already_connected_same_user(self, library: RADKit) -> None:
        """Test that reconnecting with same user returns existing service."""
        existing_service = MagicMock()
        library.direct_services["10.0.0.1-8181"] = existing_service
        library.direct_services_users["10.0.0.1-8181"] = "admin"

        with patch.dict(os.environ, {"PW": "pass"}):
            result = library.radkit_service_direct(
                username="admin",
                password="PW",
                host="10.0.0.1",
            )

        assert result == existing_service
        # service_direct should NOT be called again
        library.client.service_direct.assert_not_called()

    def test_already_connected_different_user_raises(self, library: RADKit) -> None:
        """Test that reconnecting with different user raises error."""
        existing_service = MagicMock()
        library.direct_services["10.0.0.1-8181"] = existing_service
        library.direct_services_users["10.0.0.1-8181"] = "admin"

        with patch.dict(os.environ, {"PW": "pass"}):
            with pytest.raises(
                RADKitLibraryError, match="already exists with user 'admin'"
            ):
                library.radkit_service_direct(
                    username="other_user",
                    password="PW",
                    host="10.0.0.1",
                )

    def test_password_not_in_env_raises(self, library: RADKit) -> None:
        """Test that plain string password not in env raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                RADKitLibraryError,
                match="password must be provided as Robot Secret",
            ):
                library.radkit_service_direct(
                    username="admin",
                    password="not_an_env_var",
                    host="10.0.0.1",
                )

    def test_service_direct_returns_none_raises(self, library: RADKit) -> None:
        """Test that None response from service_direct raises error."""
        library.client.service_direct.return_value.wait.return_value = None

        with patch.dict(os.environ, {"PW": "pass"}):
            with pytest.raises(
                RADKitLibraryError, match="cannot connect to service directly"
            ):
                library.radkit_service_direct(
                    username="admin",
                    password="PW",
                    host="10.0.0.1",
                )


class TestRadkitDisconnectDirectService:
    """Tests for RADKit disconnect direct service keyword."""

    def test_disconnect_specific_host(self, library: RADKit) -> None:
        """Test disconnecting a specific direct service."""
        mock_service = MagicMock()
        library.direct_services["10.0.0.1-8181"] = mock_service
        library.direct_services_users["10.0.0.1-8181"] = "admin"
        library.current_service = mock_service

        library.radkit_disconnect_direct_service(host="10.0.0.1")

        mock_service.logout.assert_called_once()
        assert "10.0.0.1-8181" not in library.direct_services
        assert library.current_service is None

    def test_disconnect_all(self, library: RADKit) -> None:
        """Test disconnecting all direct services."""
        svc1 = MagicMock()
        svc2 = MagicMock()
        library.direct_services["host1-8181"] = svc1
        library.direct_services["host2-8181"] = svc2
        library.direct_services_users["host1-8181"] = "admin"
        library.direct_services_users["host2-8181"] = "admin"
        library.current_service = svc1

        library.radkit_disconnect_direct_service()

        svc1.logout.assert_called_once()
        svc2.logout.assert_called_once()
        assert len(library.direct_services) == 0
        assert library.current_service is None

    def test_disconnect_nonexistent_raises(self, library: RADKit) -> None:
        """Test disconnecting non-existent host raises error."""
        with pytest.raises(RADKitLibraryError, match="No direct service connection"):
            library.radkit_disconnect_direct_service(host="10.0.0.1")

    def test_disconnect_all_when_empty(self, library: RADKit) -> None:
        """Test disconnecting all when no direct services exist."""
        # Should not raise
        library.radkit_disconnect_direct_service()

    def test_disconnect_preserves_cloud_service(self, library: RADKit) -> None:
        """Test that disconnecting direct services doesn't clear cloud current_service."""
        cloud_service = MagicMock()
        cloud_service.connection = MagicMock()  # cloud services have .connection
        library.current_service = cloud_service

        direct_service = MagicMock()
        library.direct_services["host1-8181"] = direct_service
        library.direct_services_users["host1-8181"] = "admin"

        library.radkit_disconnect_direct_service()

        # current_service is cloud, not direct — should be preserved
        assert library.current_service == cloud_service
