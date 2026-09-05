# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Base mixin providing shared state and client lifecycle for RADKit keywords."""

from __future__ import annotations

import os
import typing
from contextlib import ExitStack

import radkit_client as rc
from robot.libraries.BuiltIn import BuiltIn

from .utils import is_cloud_connected_service

try:
    from robot.api.types import Secret
except ImportError:
    Secret = None  # type: ignore[assignment, misc]

if typing.TYPE_CHECKING:
    from typing import Any


_UNSET = object()


class RADKitLibraryError(RuntimeError):
    """Exception raised by RADKit library keywords."""


class Base:
    """Mixin providing the RADKit client lifecycle and shared state.

    This mixin is inherited by the main ``RADKitLibrary`` library class and provides:
    - Lazy ``radkit_client.Client`` creation via ``ExitStack``
    - Cleanup via Robot Framework listener ``_close`` hook
    - Optional pyATS testbed access (when pyATS is installed and loaded)
    - Shared state: ``current_service``, ``radkit_timeout``, ``selected_devices``,
      ``current_identity``
    """

    def __init__(self) -> None:
        self._exitstack = ExitStack()
        self._client: Any = None
        self.current_service: Any = None
        self.direct_services: dict[str, Any] = {}
        self.direct_services_users: dict[str, str] = {}
        self.radkit_timeout: int = 300
        self.selected_devices: Any = None
        self.current_identity: str | None = None
        self._testbed: Any = _UNSET

        # Register self as Robot listener for cleanup
        self.ROBOT_LIBRARY_LISTENER = self
        self.ROBOT_LISTENER_API_VERSION = 3

    # --- Client lifecycle ---

    @property
    def client(self) -> Any:
        """Lazy-create the RADKit client on first access."""
        if self._client is None:
            try:
                if BuiltIn().robot_running:
                    self._client = self._create_client()
            except Exception:
                # Outside Robot context (e.g. unit tests) — allow manual assignment
                pass
        return self._client

    @client.setter
    def client(self, value: Any) -> None:
        self._client = value

    def _create_client(self) -> Any:
        """Create a radkit_client.Client via ExitStack context manager."""
        return self._exitstack.enter_context(rc.Client.create())

    def _close(self) -> None:
        """Robot listener hook: clean up on library teardown."""
        self._exitstack.close()

    # --- Optional pyATS testbed ---

    @property
    def testbed(self) -> Any:
        """Return pyATS testbed if pyats.robot.pyATSRobot is loaded, else None.

        The testbed is resolved lazily on first access and cached.
        """
        if self._testbed is _UNSET:
            try:
                pyats_robot: Any = BuiltIn().get_library_instance(
                    "pyats.robot.pyATSRobot"
                )
                self._testbed = pyats_robot.testbed
            except Exception:
                self._testbed = None
        return self._testbed

    # --- Helpers used across keyword modules ---

    def _select_service(self, serial: str | None, identity: str | None = None) -> Any:
        """Select a RADKit service by serial, or return the current service."""
        if serial:
            service = self._find_service(serial, identity)
        elif self.current_service is not None and self._is_usable_service(
            self.current_service
        ):
            service = self.current_service
        else:
            raise RADKitLibraryError(
                "No RADkit service has been selected or is connected"
            )
        return service

    def _find_service(self, serial: str, identity: str | None = None) -> Any:
        """Find a connected service by serial and optional identity."""
        services_found = []
        for service in self.client.services.values():
            if service.service_id == serial and service.connection is not None:
                if identity and service.client_id.lower() != identity.lower():
                    continue
                services_found.append(service)

        direct = self.direct_services.get(serial)
        if direct is not None:
            services_found.append(direct)

        if len(services_found) == 0:
            msg = f"No service found with serial {serial}"
            if identity:
                msg += f" and identity {identity}"
            raise KeyError(msg)
        elif len(services_found) > 1:
            raise ValueError(
                f"Multiple services found with serial {serial}, "
                "please specify an identity"
            )
        else:
            return services_found[0]

    def _find_radkit_connection(
        self,
        identity: str,
        domain: str | None = None,
        auth_type: Any = None,
    ) -> Any:
        """Search for an existing cloud connection matching identity/domain/auth_type."""
        conns_found = []
        for conn in self.client.cloud_connections.values():
            if conn.client_id.lower() == identity.lower():
                if domain and conn.domain.name.lower() != domain.lower():
                    continue
                if auth_type and conn.type != auth_type:
                    continue
                conns_found.append(conn)
        if len(conns_found) == 1:
            return conns_found[0]
        elif len(conns_found) > 1:
            raise NotImplementedError(
                "RADKit library does not support multiple connections "
                "for the same identity"
            )
        else:
            raise ValueError(
                f"No authenticated cloud connection found for identity '{identity}'"
            )

    @staticmethod
    def _get_secret_or_env_only(value: Any, arg_name: str) -> str | None:
        """Resolve a value that must be a Robot Secret or env-var name.

        Returns the resolved string value, or None if value is None.
        Raises RADKitLibraryError if value is a plain string that is not
        an environment variable name.
        """
        if value is None:
            return None
        if Secret is not None and isinstance(value, Secret):
            return str(value.value)
        if isinstance(value, str) and value in os.environ:
            return os.environ[value]
        raise RADKitLibraryError(
            f"{arg_name} must be provided as Robot Secret or as an "
            "environment variable name"
        )

    def _is_direct_service(self, service: Any) -> bool:
        """Check if a service is a direct service."""
        return service in self.direct_services.values()

    def _is_usable_service(self, service: Any) -> bool:
        """Check if a service is usable (cloud-connected or direct)."""
        return is_cloud_connected_service(service) or self._is_direct_service(service)

    def _get_devices(self, devices: Any, inventory: Any = None) -> Any:
        """Resolve devices argument to a RADKit DeviceDict."""
        if devices is None:
            if self.selected_devices is not None:
                return self.selected_devices
            else:
                raise ValueError(
                    "no devices have been passed, and none have been selected prior"
                )
        elif isinstance(devices, str):
            subset = devices.split(";")
        elif isinstance(devices, list):
            subset = devices
        else:
            # Assume it's a DeviceDict or similar RADKit object — pass through
            return devices

        if not inventory:
            if self.current_service is None:
                raise RADKitLibraryError(
                    "No RADkit service has been selected/connected"
                )
            inventory = self.current_service.inventory
        return inventory.subset(subset)

    def _get_timeout(self, timeout: int | str | None) -> int:
        """Return the given timeout as int, or fall back to radkit_timeout."""
        if timeout:
            return int(timeout)
        else:
            return self.radkit_timeout
