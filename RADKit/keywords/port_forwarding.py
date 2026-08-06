# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Port forwarding keywords for RADKit Robot Framework library."""

from __future__ import annotations

import ipaddress
import typing

import radkit_client.sync.port_forwarding
from robot.api import logger
from robot.api.deco import keyword

from RADKit.base import RADKitLibraryError
from RADKit.utils import is_ipv6_address

if typing.TYPE_CHECKING:
    from typing import Any


class PortForwardingKeywords:
    """Keywords for RADKit TCP port forwarding to remote devices."""

    @keyword("RADKit Port Forward to Device")
    def radkit_device_port_forward(
        self,
        device: str,
        local_port: int,
        destination_port: int,
        serial: str | None = None,
        identity: str | None = None,
        testbed_device: str | None = None,
        testbed_conn: str | None = None,
    ) -> tuple[Any, int]:
        """<p>Set up TCP port forwarding to a remote RADKit device. This allows
            direct interaction with the device's port on the local host.</p>

            <p>For security, the forwarded port is only reachable from localhost.</p>

            <p>The <code>testbed_device</code> and <code>testbed_conn</code>
            parameters are optional and require pyATS to be installed and the
            <code>pyats.robot.pyATSRobot</code> library to be loaded. When provided,
            the testbed device's connection entry will be updated to point to the
            port forward.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>device</code>: RADKit device name</li>
                <li><code>local_port</code>: Local port (use 0 for auto-assign)</li>
                <li><code>destination_port</code>: Remote device port</li>
                <li><code>serial</code>: Service serial (optional)</li>
                <li><code>identity</code>: RADKit identity (optional)</li>
                <li><code>testbed_device</code>: pyATS testbed device name to update
                    (optional, requires pyATS)</li>
                <li><code>testbed_conn</code>: Testbed connection entry to update
                    (required when testbed_device is set)</li>
            </ul>

            <p><strong>Returns:</strong> Tuple of (forwarder object, local port)</p>

            <p><strong>Example:</strong></p>
            <pre>
        RADKit select service    1111-2222-3333
        ${forwarder}    ${port}=    RADKit Port Forward to Device
        ...    server1    local_port=0    destination_port=8443

        # With pyATS testbed integration:
        RADKit Port Forward to Device    linuxdevice    local_port=0
        ...    destination_port=22    testbed_device=linux_server
        ...    testbed_conn=cli
            </pre>
        """
        service = self._select_service(serial, identity)  # type: ignore[attr-defined]
        try:
            radkit_device = service.inventory[device]
        except KeyError:
            raise RADKitLibraryError(f"Unknown device: {device}") from None

        # Validate testbed args before setting up port forward
        connhandle = self._get_connhandle(testbed_device, testbed_conn)

        forwarder = radkit_device.forward_tcp_port(
            local_port=local_port,
            destination_port=destination_port,
            local_address="127.0.0.1",
        )
        logger.debug(str(forwarder))

        ipv4_port = self._retrieve_dynamic_local_port(forwarder)
        logger.info(f"Port forwarding created, local port: {ipv4_port}")

        if connhandle:
            connhandle["ip"] = ipaddress.IPv4Address("127.0.0.1")
            connhandle["host"] = "localhost"
            connhandle["port"] = ipv4_port
            logger.info(
                "modified testbed device connection entry device {} connection {} "
                "to '{}:{}'".format(
                    testbed_device, testbed_conn, connhandle["ip"], connhandle["port"]
                )
            )

        return forwarder, ipv4_port

    def _retrieve_dynamic_local_port(self, forwarder: Any) -> int:
        """Get the actual local port from the forwarder (handles dynamic port 0)."""
        if (
            forwarder.status
            != radkit_client.sync.port_forwarding.PortForwarderStatus.RUNNING
        ):
            raise RADKitLibraryError("Forwarder is not active/running")

        if forwarder.local_port == 0:
            ipv4_port = 0
            # TODO: replace with public API to retrieve dynamic ports
            # https://gitlab-sjc.cisco.com/lazy_maestro/standalone/-/issues/3376
            dynamic_ports = forwarder._async_object.get_dynamic_local_ports()
            for k, v in dynamic_ports.items():
                if not is_ipv6_address(k):
                    ipv4_port = v
                    break
            else:
                raise RADKitLibraryError("Could not find dynamic IPv4 port")
        else:
            ipv4_port = forwarder.local_port

        return int(ipv4_port)

    def _get_connhandle(self, device: str | None, connection: str | None) -> Any:
        """Get pyATS testbed connection handle, or None if not requested.

        Raises RADKitLibraryError if testbed_device is set but pyATS is not available.
        """
        if device is not None:
            if not connection:
                raise ValueError(
                    "Error, testbed_conn is required parameter when device is set"
                )
            testbed = self.testbed  # type: ignore[attr-defined]
            if testbed is None:
                raise RADKitLibraryError(
                    "testbed_device requires pyATS to be installed and "
                    "'Library  pyats.robot.pyATSRobot' loaded in your test suite"
                )
            try:
                connhandle = testbed.devices[device].connections[connection]
            except (KeyError, AttributeError):
                raise RADKitLibraryError(
                    f"Error, device {device} is not defined in topology yaml file "
                    f"or has no connections attribute {connection}"
                ) from None
        else:
            connhandle = None

        return connhandle

    @keyword("RADKit Stop Port Forward")
    def radkit_stop_port_forward(self, forwarder: Any) -> None:
        """<p>Stop port forwarding to a remote RADKit device.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>forwarder</code>: Port forwarder object returned by
                    "RADKit Port Forward to Device"</li>
            </ul>

            <p><strong>Example:</strong></p>
            <pre>
        ${forwarder}    ${port}=    RADKit Port Forward to Device
        ...    server1    local_port=0    destination_port=8443
        # ... do something ...
        RADKit Stop Port Forward    ${forwarder}
            </pre>
        """
        forwarder.stop()
