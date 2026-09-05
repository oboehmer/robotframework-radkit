# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Utility functions for RADKit Robot Framework library."""

from __future__ import annotations

import ipaddress
import typing

if typing.TYPE_CHECKING:
    from typing import Any


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


def direct_service_id(host: str, port: int) -> str:
    """Return a unique key for a direct service connection."""
    return f"{host}-{port}"


def is_cloud_connected_service(service: Any) -> bool:
    """Check if a service is a cloud-connected service."""
    return getattr(service, "connection", None) is not None
