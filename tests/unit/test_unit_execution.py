# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Unit tests for execution keywords."""

from unittest.mock import MagicMock, patch

import pytest
import radkit_client.sync.exceptions

from RADKitLibrary import RADKitLibrary, RADKitLibraryError


@pytest.fixture
def library() -> RADKitLibrary:
    """Create a RADKit library instance."""
    with patch("RADKitLibrary.base.BuiltIn"):
        lib = RADKitLibrary()
        lib._client = MagicMock()
        return lib


class TestRadkitExecute:
    """Tests for RADKit execute keyword."""

    def test_single_command_single_device(self, library: RADKitLibrary) -> None:
        """Test executing a single command on one device."""
        mock_devices = MagicMock()
        mock_result = MagicMock()
        mock_result.full_result = {
            "router1": {"show version": MagicMock(data="Cisco IOS XE Version 17.3.1")}
        }
        mock_devices.exec.return_value.wait.return_value = mock_result
        library.selected_devices = mock_devices

        result = library.radkit_execute_sync("show version")
        assert "router1" in result
        assert result["router1"] == "Cisco IOS XE Version 17.3.1"

    def test_multiple_commands(self, library: RADKitLibrary) -> None:
        """Test executing multiple commands."""
        mock_devices = MagicMock()
        mock_result = MagicMock()
        mock_result.full_result = {
            "router1": {
                "show version": MagicMock(data="version info"),
                "show clock": MagicMock(data="12:00:00"),
            }
        }
        mock_devices.exec.return_value.wait.return_value = mock_result
        library.selected_devices = mock_devices

        result = library.radkit_execute_sync(["show version", "show clock"])
        assert result["router1"]["show version"] == "version info"
        assert result["router1"]["show clock"] == "12:00:00"

    def test_all_commands_failed_raises(self, library: RADKitLibrary) -> None:
        """Test that failure of all commands raises RADKitLibraryError."""
        mock_devices = MagicMock()
        mock_result = MagicMock()

        # Use the real ClientError class so it matches the except clause
        client_error_cls = radkit_client.sync.exceptions.ClientError

        mock_cmd_result = MagicMock()
        type(mock_cmd_result).data = property(
            lambda self: (_ for _ in ()).throw(client_error_cls("fail"))
        )

        mock_result.full_result = {"router1": {"show version": mock_cmd_result}}
        mock_devices.exec.return_value.wait.return_value = mock_result
        library.selected_devices = mock_devices

        with pytest.raises(
            RADKitLibraryError, match="No command was successfully executed"
        ):
            library.radkit_execute_sync("show version")

    def test_raw_output(self, library: RADKitLibrary) -> None:
        """Test raw=True returns the raw RADKit result."""
        mock_devices = MagicMock()
        mock_result = MagicMock()
        mock_result.full_result = {
            "router1": {"show version": MagicMock(data="version info")}
        }
        mock_devices.exec.return_value.wait.return_value = mock_result
        library.selected_devices = mock_devices

        result = library.radkit_execute_sync("show version", raw=True)
        assert result == mock_result

    def test_custom_timeout(self, library: RADKitLibrary) -> None:
        """Test custom execution timeout is passed through."""
        mock_devices = MagicMock()
        mock_result = MagicMock()
        mock_result.full_result = {"router1": {"show version": MagicMock(data="info")}}
        mock_devices.exec.return_value.wait.return_value = mock_result
        library.selected_devices = mock_devices

        library.radkit_execute_sync("show version", exec_timeout=60)
        mock_devices.exec.assert_called_once_with("show version", timeout=60)

    def test_no_devices_raises(self, library: RADKitLibrary) -> None:
        """Test that missing devices raises ValueError."""
        library.selected_devices = None
        with pytest.raises(ValueError, match="no devices have been passed"):
            library.radkit_execute_sync("show version")
