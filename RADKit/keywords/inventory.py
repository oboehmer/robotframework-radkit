# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Inventory-related keywords for RADKit Robot Framework library."""

from __future__ import annotations

import typing

from robot.api import logger
from robot.api.deco import keyword
from robot.utils import is_truthy

if typing.TYPE_CHECKING:
    from typing import Any


class InventoryKeywords:
    """Keywords for RADKit device inventory and device selection."""

    @keyword("RADKit device inventory")
    def radkit_retrieve_inventory(
        self,
        serial: str | None = None,
        identity: str | None = None,
        filter: str | None = None,
        raw: bool = False,
        update: bool = False,
    ) -> Any:
        """<p>Retrieve the device inventory of the specified RADKit service
            (or the currently selected service if serial is not specified).</p>

            <p>By default, returns the inventory as a list of device names. Set
            <code>raw=True</code> to return the RADKit DeviceDict type for
            lower-level manipulation.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>serial</code>: Service serial (optional, defaults to
                    currently selected service)</li>
                <li><code>identity</code>: Optional RADKit identity to use</li>
                <li><code>filter</code>: Filter expression, e.g.
                    <code>name,PE.*</code> or <code>type,IOS</code></li>
                <li><code>update</code>: When True, performs update_inventory()
                    before fetching</li>
                <li><code>raw</code>: When True, returns RADKit DeviceDict type</li>
            </ul>

            <p><strong>Returns:</strong> List of device names, or DeviceDict if
            raw=True</p>

            <p><strong>Example:</strong></p>
            <pre>
        @{devices}=    RADKit device inventory

        @{devices}=    RADKit device inventory    1234-abcd-efgh
        @{devices}=    RADKit device inventory    filter=name,PE.*
        @{devices}=    RADKit device inventory    filter=type,IO.*
            </pre>
        """
        service = self._select_service(serial, identity)  # type: ignore[attr-defined]
        if update:
            logger.debug("Requesting updated inventory")
            service.update_inventory()
        if filter is None:
            result = service.inventory
        else:
            key, value = filter.split(",", maxsplit=1)
            result = service.inventory.filter(key, value)
        if is_truthy(raw):
            return result
        else:
            return list(result)

    @keyword("RADKit select devices")
    def radkit_select_devices(
        self,
        devices: Any,
        serial: str | None = None,
        identity: str | None = None,
    ) -> Any:
        """<p>Select one or more RADKit devices as default for subsequent
            RADKit execute calls.</p>

            <p>Devices can be passed as a semicolon-separated string
            (<code>device1;device2;device3</code>), a list of strings, or a RADKit
            DeviceDict structure.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>devices</code>: Device(s) to select (str, list, or
                    DeviceDict)</li>
                <li><code>serial</code>: Service serial (optional)</li>
                <li><code>identity</code>: Optional RADKit identity to use</li>
            </ul>

            <p><strong>Returns:</strong> DeviceDict of selected devices</p>

            <p><strong>Example:</strong></p>
            <pre>
        @{devices}=    Create List    router1    router2    router3
        ${result}=    RADKit select devices    ${devices}

        ${result}=    RADKit select devices    router1;router2;router3

        ${inventory}=    RADKit device inventory    raw=True
        ${subset}=    Evaluate    $inventory.filter("name", "PE*")
        ${result}=    RADKit select devices    ${subset}
            </pre>
        """
        inventory = self.radkit_retrieve_inventory(
            serial=serial, identity=identity, raw=True
        )
        self.selected_devices = self._get_devices(devices, inventory)  # type: ignore[attr-defined]
        return self.selected_devices
