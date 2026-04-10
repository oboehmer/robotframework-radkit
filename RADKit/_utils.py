# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Utility functions for RADKit Robot Framework library."""

import ipaddress


def is_ipv6_address(address: str) -> bool:
    """Check if the given address string is an IPv6 address.

    Args:
        address: IP address string to check.

    Returns:
        True if the address is IPv6, False otherwise.
    """
    try:
        return isinstance(ipaddress.ip_address(address), ipaddress.IPv6Address)
    except ValueError:
        return False
