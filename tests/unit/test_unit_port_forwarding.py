# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Unit tests for port forwarding keywords."""

from unittest.mock import MagicMock, patch

import pytest
import radkit_client.sync.port_forwarding

from RADKitLibrary import RADKitLibrary, RADKitLibraryError


@pytest.fixture
def library() -> RADKitLibrary:
    """Create a RADKit library instance."""
    with patch("RADKitLibrary.base.BuiltIn"):
        lib = RADKitLibrary()
        lib._client = MagicMock()
        return lib


class TestRadkitPortForward:
    """Tests for RADKit Port Forward to Device keyword."""

    def test_port_forward_basic(self, library: RADKitLibrary) -> None:
        """Test basic port forwarding setup."""
        mock_service = MagicMock()
        mock_device = MagicMock()
        mock_service.inventory = {"server1": mock_device}
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        mock_forwarder = MagicMock()
        mock_forwarder.status = (
            radkit_client.sync.port_forwarding.PortForwarderStatus.RUNNING
        )
        mock_forwarder.local_port = 8443
        mock_device.forward_tcp_port.return_value = mock_forwarder

        forwarder, port = library.radkit_device_port_forward(
            "server1", local_port=8443, destination_port=443
        )
        assert forwarder == mock_forwarder
        assert port == 8443

    def test_port_forward_dynamic_port(self, library: RADKitLibrary) -> None:
        """Test port forwarding with dynamic port (local_port=0)."""
        mock_service = MagicMock()
        mock_device = MagicMock()
        mock_service.inventory = {"server1": mock_device}
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        mock_forwarder = MagicMock()
        mock_forwarder.status = (
            radkit_client.sync.port_forwarding.PortForwarderStatus.RUNNING
        )
        mock_forwarder.local_port = 0
        mock_forwarder._async_object.get_dynamic_local_ports.return_value = {
            "127.0.0.1": 54321,
            "::1": 54322,
        }
        mock_device.forward_tcp_port.return_value = mock_forwarder

        forwarder, port = library.radkit_device_port_forward(
            "server1", local_port=0, destination_port=22
        )
        assert port == 54321

    def test_unknown_device_raises(self, library: RADKitLibrary) -> None:
        """Test that unknown device raises RADKitLibraryError."""
        mock_service = MagicMock()
        # Use MagicMock for inventory to allow setting __getitem__
        mock_inventory = MagicMock()
        mock_inventory.__getitem__ = MagicMock(side_effect=KeyError("unknown"))
        mock_service.inventory = mock_inventory
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        with pytest.raises(RADKitLibraryError, match="Unknown device"):
            library.radkit_device_port_forward(
                "unknown_device", local_port=0, destination_port=22
            )

    def test_testbed_device_without_pyats_raises(self, library: RADKitLibrary) -> None:
        """Test that testbed_device without pyATS raises RADKitLibraryError."""
        mock_service = MagicMock()
        mock_device = MagicMock()
        mock_service.inventory = {"server1": mock_device}
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        mock_forwarder = MagicMock()
        mock_forwarder.status = (
            radkit_client.sync.port_forwarding.PortForwarderStatus.RUNNING
        )
        mock_forwarder.local_port = 8443
        mock_device.forward_tcp_port.return_value = mock_forwarder

        # testbed is None (pyATS not available)
        library._testbed = None

        with pytest.raises(RADKitLibraryError, match="testbed_device requires pyATS"):
            library.radkit_device_port_forward(
                "server1",
                local_port=0,
                destination_port=22,
                testbed_device="linux_server",
                testbed_conn="cli",
            )

    def test_testbed_conn_required(self, library: RADKitLibrary) -> None:
        """Test that testbed_conn is required when testbed_device is set."""
        mock_service = MagicMock()
        mock_service.inventory = {"server1": MagicMock()}
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        with pytest.raises(ValueError, match="testbed_conn is required"):
            library.radkit_device_port_forward(
                "server1",
                local_port=0,
                destination_port=22,
                testbed_device="linux_server",
            )


class TestRadkitStopPortForward:
    """Tests for RADKit Stop Port Forward keyword."""

    def test_stop_port_forward(self, library: RADKitLibrary) -> None:
        """Test stopping port forwarding."""
        mock_forwarder = MagicMock()
        library.radkit_stop_port_forward(mock_forwarder)
        mock_forwarder.stop.assert_called_once()
