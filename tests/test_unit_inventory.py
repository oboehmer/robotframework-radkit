# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Unit tests for inventory keywords."""

from unittest.mock import MagicMock, patch

import pytest

from RADKit import RADKit


@pytest.fixture
def library() -> RADKit:
    """Create a RADKit library instance."""
    with patch("RADKit._base.BuiltIn"):
        lib = RADKit()
        lib._client = MagicMock()
        return lib


class TestRadkitDeviceInventory:
    """Tests for RADKit device inventory keyword."""

    def test_returns_device_list(self, library: RADKit) -> None:
        """Test that inventory returns list of device names by default."""
        mock_service = MagicMock()
        mock_service.inventory.__iter__ = MagicMock(
            return_value=iter(["router1", "router2", "switch1"])
        )
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        result = library.radkit_retrieve_inventory()
        assert result == ["router1", "router2", "switch1"]

    def test_returns_raw_inventory(self, library: RADKit) -> None:
        """Test that inventory returns DeviceDict when raw=True."""
        mock_service = MagicMock()
        mock_inventory = MagicMock()
        mock_service.inventory = mock_inventory
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        result = library.radkit_retrieve_inventory(raw=True)
        assert result == mock_inventory

    def test_filter_inventory(self, library: RADKit) -> None:
        """Test inventory filtering."""
        mock_service = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.__iter__ = MagicMock(return_value=iter(["PE-router1"]))
        mock_service.inventory.filter.return_value = mock_filtered
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        result = library.radkit_retrieve_inventory(filter="name,PE.*")
        mock_service.inventory.filter.assert_called_once_with("name", "PE.*")
        assert result == ["PE-router1"]

    def test_update_inventory(self, library: RADKit) -> None:
        """Test inventory update before fetch."""
        mock_service = MagicMock()
        mock_service.inventory.__iter__ = MagicMock(return_value=iter([]))
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        library.radkit_retrieve_inventory(update=True)
        mock_service.update_inventory.assert_called_once()

    def test_with_serial(self, library: RADKit) -> None:
        """Test inventory with specific service serial."""
        mock_service = MagicMock()
        mock_service.service_id = "test-serial"
        mock_service.connection = MagicMock()
        mock_service.client_id = "user@cisco.com"
        mock_service.inventory.__iter__ = MagicMock(return_value=iter(["dev1"]))

        library.client.services.values.return_value = [mock_service]
        library.current_identity = "user@cisco.com"

        result = library.radkit_retrieve_inventory(serial="test-serial")
        assert result == ["dev1"]


class TestRadkitSelectDevices:
    """Tests for RADKit select devices keyword."""

    def test_select_devices_string(self, library: RADKit) -> None:
        """Test selecting devices from semicolon-separated string."""
        mock_service = MagicMock()
        mock_inventory = MagicMock()
        mock_subset = MagicMock()
        mock_inventory.subset.return_value = mock_subset
        mock_service.inventory = mock_inventory
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        result = library.radkit_select_devices("router1;router2")

        assert result == mock_subset
        assert library.selected_devices == mock_subset

    def test_select_devices_list(self, library: RADKit) -> None:
        """Test selecting devices from list."""
        mock_service = MagicMock()
        mock_inventory = MagicMock()
        mock_subset = MagicMock()
        mock_inventory.subset.return_value = mock_subset
        mock_service.inventory = mock_inventory
        mock_service.connection = MagicMock()
        library.current_service = mock_service

        result = library.radkit_select_devices(["router1", "router2"])

        assert result == mock_subset
