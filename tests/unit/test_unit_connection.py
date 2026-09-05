# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Unit tests for connection keywords."""

import base64
import os
from unittest.mock import MagicMock, patch

import pytest
import radkit_client

from RADKitLibrary import RADKitLibrary, RADKitLibraryError


@pytest.fixture
def library() -> RADKitLibrary:
    """Create a RADKit library instance."""
    with patch("RADKitLibrary.base.BuiltIn"):
        lib = RADKitLibrary()
        lib._client = MagicMock()
        return lib


class TestRadkitClientVersion:
    """Tests for RADKit Client Version keyword."""

    def test_returns_version_string(self, library: RADKitLibrary) -> None:
        """Test that version string is returned."""
        with patch("radkit_client.version.version_str", "1.9.6"):
            result = library.radkit_client_version()
            assert result == "1.9.6"


class TestRadkitCertificateLogin:
    """Tests for RADKit certificate login keyword."""

    def test_already_connected_returns_client(self, library: RADKitLibrary) -> None:
        """Test that already connected identity returns existing client."""
        mock_conn = MagicMock()
        mock_conn.client_id = "user@cisco.com"
        mock_conn.domain.name = "PROD"
        mock_conn.type = radkit_client.AuthFlowType.CERTIFICATE

        library.client.cloud_connections.values.return_value = [mock_conn]

        result = library.radkit_certificate_login(
            identity="user@cisco.com",
            private_key_password="test_password",
        )
        assert result == library.client

    def test_missing_password_raises(self, library: RADKitLibrary) -> None:
        """Test that missing password raises RADKitLibraryError."""
        library.client.cloud_connections.values.return_value = []

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                RADKitLibraryError, match="Could not find private key password"
            ):
                library.radkit_certificate_login(identity="user@cisco.com")

    def test_password_from_env_base64(self, library: RADKitLibrary) -> None:
        """Test password resolution from base64 env var."""
        password = "my_secret"
        b64_password = base64.b64encode(password.encode()).decode()

        library.client.cloud_connections.values.return_value = []

        with patch.dict(
            os.environ,
            {"RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64": b64_password},
            clear=True,
        ):
            library.radkit_certificate_login(identity="user@cisco.com")
            library.client.certificate_login.assert_called_once()
            call_kwargs = library.client.certificate_login.call_args[1]
            assert call_kwargs["private_key_password"] == password

    def test_password_from_env_cleartext(self, library: RADKitLibrary) -> None:
        """Test password resolution from cleartext env var."""
        library.client.cloud_connections.values.return_value = []

        with patch.dict(
            os.environ,
            {"RADKIT_CLIENT_PRIVATE_KEY_PASSWORD": "cleartext_pw"},
            clear=True,
        ):
            library.radkit_certificate_login(identity="user@cisco.com")
            call_kwargs = library.client.certificate_login.call_args[1]
            assert call_kwargs["private_key_password"] == "cleartext_pw"

    def test_password_literal_string_rejected(self, library: RADKitLibrary) -> None:
        """Test that passing a literal password string raises RADKitLibraryError."""
        library.client.cloud_connections.values.return_value = []

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                RADKitLibraryError,
                match="does not match any environment variable name",
            ):
                library.radkit_certificate_login(
                    identity="user@cisco.com",
                    private_key_password="literal_password_value",
                )

    def test_password_from_named_env_var_argument(self, library: RADKitLibrary) -> None:
        """Test password resolution when passing env var name as argument."""
        library.client.cloud_connections.values.return_value = []

        with patch.dict(
            os.environ,
            {"MY_PASSWORD_VAR": "secret_from_env"},
            clear=True,
        ):
            library.radkit_certificate_login(
                identity="user@cisco.com",
                private_key_password="MY_PASSWORD_VAR",
            )
            call_kwargs = library.client.certificate_login.call_args[1]
            assert call_kwargs["private_key_password"] == "secret_from_env"

    def test_password_from_secret_type(self, library: RADKitLibrary) -> None:
        """Test password resolution when passing a Robot Framework Secret."""
        from robot.api.types import Secret

        library.client.cloud_connections.values.return_value = []

        with patch.dict(os.environ, {}, clear=True):
            library.radkit_certificate_login(
                identity="user@cisco.com",
                private_key_password=Secret("s3cret"),
            )
            call_kwargs = library.client.certificate_login.call_args[1]
            assert call_kwargs["private_key_password"] == "s3cret"

    def test_sets_current_identity(self, library: RADKitLibrary) -> None:
        """Test that current_identity is set after login."""
        library.client.cloud_connections.values.return_value = []

        with patch.dict(os.environ, {"PW_VAR": "pw"}):
            library.radkit_certificate_login(
                identity="user@cisco.com",
                private_key_password="PW_VAR",
            )
        assert library.current_identity == "user@cisco.com"

    def test_env_paths_used_as_defaults(self, library: RADKitLibrary) -> None:
        """Test that RADKIT_* env vars are used as fallback for paths/identity."""
        library.client.cloud_connections.values.return_value = []

        env = {
            "RADKIT_IDENTITY": "env_identity",
            "RADKIT_CERT_PATH": "env_cert",
            "RADKIT_CA_PATH": "env_ca",
            "RADKIT_KEY_PATH": "env_key",
            "MY_PW": "the_password",
        }
        with patch.dict(os.environ, env, clear=True):
            library.radkit_certificate_login(
                private_key_password="MY_PW",
                domain="domain",
            )

        library.client.certificate_login.assert_called_once_with(
            identity="env_identity",
            cert_path="env_cert",
            ca_path="env_ca",
            key_path="env_key",
            private_key_password="the_password",
            domain="domain",
        )

    def test_explicit_args_override_env_paths(self, library: RADKitLibrary) -> None:
        """Test that explicit keyword args take precedence over env vars."""
        library.client.cloud_connections.values.return_value = []

        env = {
            "RADKIT_IDENTITY": "env_identity",
            "RADKIT_CERT_PATH": "env_cert",
            "RADKIT_CA_PATH": "env_ca",
            "RADKIT_KEY_PATH": "env_key",
            "MY_PW": "the_password",
        }
        with patch.dict(os.environ, env, clear=True):
            library.radkit_certificate_login(
                identity="my_identity",
                cert_path="my_cert",
                ca_path="my_ca",
                key_path="my_key",
                private_key_password="MY_PW",
                domain="domain",
            )

        library.client.certificate_login.assert_called_once_with(
            identity="my_identity",
            cert_path="my_cert",
            ca_path="my_ca",
            key_path="my_key",
            private_key_password="the_password",
            domain="domain",
        )


class TestRadkitDisconnect:
    """Tests for RADKit disconnect keyword."""

    def test_disconnect_all(self, library: RADKitLibrary) -> None:
        """Test disconnecting all connections."""
        conn1 = MagicMock()
        conn2 = MagicMock()

        # Create a simple mock for cloud_connections
        mock_cloud_connections = MagicMock()
        mock_cloud_connections.values.return_value = [conn1, conn2]
        # First check should return 2, second check should return 0
        mock_cloud_connections.__len__ = MagicMock(side_effect=[2, 0])
        library.client.cloud_connections = mock_cloud_connections

        library.radkit_disconnect()
        conn1.logout.assert_called_once()
        conn2.logout.assert_called_once()

    def test_disconnect_by_identity(self, library: RADKitLibrary) -> None:
        """Test disconnecting a specific identity."""
        conn = MagicMock()
        conn.client_id = "user@cisco.com"
        conn.domain.name = "PROD"
        conn.type = "CERTIFICATE"
        library.client.cloud_connections.values.return_value = [conn]
        library.client.cloud_connections.__len__ = MagicMock(return_value=0)

        library.radkit_disconnect(identity="user@cisco.com")
        conn.logout.assert_called_once()

    def test_disconnect_no_connections(self, library: RADKitLibrary) -> None:
        """Test disconnect when no connections exist."""
        library.client.cloud_connections.values.return_value = []
        library.client.cloud_connections.__len__ = MagicMock(return_value=0)
        # Should not raise
        library.radkit_disconnect()


class TestRadkitSelectService:
    """Tests for RADKit select service keyword."""

    def test_select_existing_service(self, library: RADKitLibrary) -> None:
        """Test selecting an already connected service."""
        mock_service = MagicMock()
        mock_service.service_id = "abcd-1234-efgh"
        mock_service.connection = MagicMock()
        mock_service.client_id = "user@cisco.com"
        mock_service.serial = "abcd-1234-efgh"

        library.client.services.values.return_value = [mock_service]
        library.current_identity = "user@cisco.com"

        result = library.radkit_select_service("abcd-1234-efgh")
        assert result == mock_service
        assert library.current_service == mock_service

    def test_select_new_service(self, library: RADKitLibrary) -> None:
        """Test connecting to a new service."""
        library.client.services.values.return_value = []
        library.current_identity = "user@cisco.com"

        mock_conn = MagicMock()
        mock_conn.client_id = "user@cisco.com"
        mock_conn.domain.name = "PROD"
        mock_conn.type = "CERTIFICATE"
        library.client.cloud_connections.values.return_value = [mock_conn]

        mock_service = MagicMock()
        mock_service.serial = "abcd-1234-efgh"
        library.client.service.return_value.wait.return_value = mock_service

        result = library.radkit_select_service("abcd-1234-efgh")
        assert result == mock_service


class TestRadkitTimeout:
    """Tests for RADKit timeout keyword."""

    def test_set_timeout(self, library: RADKitLibrary) -> None:
        """Test setting timeout returns old value."""
        assert library.radkit_timeout == 300
        old = library.set_radkit_timeout(60)
        assert old == 300
        assert library.radkit_timeout == 60

    def test_set_timeout_string(self, library: RADKitLibrary) -> None:
        """Test setting timeout with string value."""
        library.set_radkit_timeout("120")
        assert library.radkit_timeout == 120
