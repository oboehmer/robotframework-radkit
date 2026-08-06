# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Unit tests for Genie keywords."""

from unittest.mock import MagicMock, patch

import pytest
import radkit_client.sync
import radkit_genie

from RADKit import RADKit
from RADKit.base import RADKitLibraryError


@pytest.fixture
def library() -> RADKit:
    """Create a RADKit library instance."""
    with patch("RADKit.base.BuiltIn"):
        lib = RADKit()
        lib._client = MagicMock()
        return lib


class TestRadkitGenieParse:
    """Tests for RADKit Genie Parse keyword."""

    def test_parse_with_commands(self, library: RADKit) -> None:
        """Test parsing with commands and devices."""
        mock_devices = MagicMock()
        mock_result = MagicMock()
        mock_result.full_result = {
            "router1": {"show version": MagicMock(data="version info")}
        }
        mock_devices.exec.return_value.wait.return_value = mock_result
        library.selected_devices = mock_devices

        mock_parsed = MagicMock()

        with (
            patch.object(radkit_genie, "parse", return_value=mock_parsed),
            patch.object(
                radkit_genie,
                "parsed_to_dict",
                return_value={"router1": {"show version": {"version": "17.3.1"}}},
            ),
        ):
            result = library.radkit_genie_parse(
                commands="show version", devices=mock_devices, os="iosxe"
            )

        assert "router1" in result

    def test_parse_with_raw_output(self, library: RADKit) -> None:
        """Test parsing with raw output from previous execute."""
        # Create a mock that is an instance of ExecResponseBase
        mock_raw = MagicMock(spec=radkit_client.sync.ExecResponseBase)

        with (
            patch.object(radkit_genie, "parse", return_value=MagicMock()),
            patch.object(
                radkit_genie,
                "parsed_to_dict",
                return_value={"router1": {"show version": {}}},
            ),
        ):
            result = library.radkit_genie_parse(raw_output=mock_raw, os="iosxe")

        assert "router1" in result

    def test_parse_commands_and_raw_raises(self, library: RADKit) -> None:
        """Test that passing both commands and raw_output raises."""
        with pytest.raises(ValueError, match="either pass commands"):
            library.radkit_genie_parse(
                commands="show version",
                raw_output=MagicMock(),
            )

    def test_parse_invalid_raw_raises(self, library: RADKit) -> None:
        """Test that invalid raw_output type raises."""
        with pytest.raises(ValueError, match="not a raw RADKit result"):
            library.radkit_genie_parse(raw_output="not_a_result")


class TestRadkitGenieLearn:
    """Tests for RADKit Genie Learn keyword."""

    def test_learn_single_model(self, library: RADKit) -> None:
        """Test learning a single model."""
        mock_devices = MagicMock()
        library.selected_devices = mock_devices

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"router1": {"routing": {"info": {}}}}

        with patch.object(radkit_genie, "learn", return_value=mock_result):
            result = library.radkit_genie_learn("routing", os="iosxe")

        assert "router1" in result

    def test_learn_multiple_models(self, library: RADKit) -> None:
        """Test learning multiple models."""
        mock_devices = MagicMock()
        library.selected_devices = mock_devices

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {"router1": {"routing": {}, "platform": {}}}

        with patch.object(radkit_genie, "learn", return_value=mock_result):
            result = library.radkit_genie_learn(["routing", "platform"], os="iosxe")

        assert result["router1"]["routing"] == {}
        assert result["router1"]["platform"] == {}

    def test_learn_invalid_models_type(self, library: RADKit) -> None:
        """Test that invalid models type raises ValueError."""
        library.selected_devices = MagicMock()

        with pytest.raises(ValueError, match="expected a single model"):
            library.radkit_genie_learn(123)  # type: ignore[arg-type]


class TestRadkitGenieFingerprint:
    """Tests for RADKit Genie Fingerprint keyword."""

    def test_fingerprint(self, library: RADKit) -> None:
        """Test fingerprinting devices."""
        mock_devices = MagicMock()
        library.selected_devices = mock_devices

        with patch.object(
            radkit_genie,
            "fingerprint",
            return_value={"router1": "iosxe", "router2": "iosxr"},
        ):
            result = library.radkit_genie_fingerprint(mock_devices)

        assert result["router1"] == "iosxe"


class TestGenieNotInstalled:
    """Tests for Genie keywords when radkit_genie is not installed."""

    def test_genie_parse_not_installed(self) -> None:
        """Test that Genie Parse raises when radkit_genie is not installed."""
        with patch("RADKit.base.BuiltIn"):
            lib = RADKit()
            lib._client = MagicMock()

            with patch("RADKit.keywords.genie.radkit_genie", None):
                with pytest.raises(
                    RADKitLibraryError, match="cisco-radkit-genie is required"
                ):
                    lib.radkit_genie_parse(commands="show version")
