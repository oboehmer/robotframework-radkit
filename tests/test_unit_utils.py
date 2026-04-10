# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Unit tests for utility functions."""

import pytest

from RADKit._utils import is_ipv6_address


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ("::1", True),
        ("2001:db8::1", True),
        ("127.0.0.1", False),
        ("192.168.1.1", False),
        ("not_an_ip", False),
        ("", False),
    ],
)
def test_is_ipv6_address(address: str, expected: bool) -> None:
    assert is_ipv6_address(address) is expected
