# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Execution-related keywords for RADKit Robot Framework library."""

from __future__ import annotations

import typing

import radkit_client.sync.exceptions
from robot.api import logger
from robot.api.deco import keyword
from robot.utils import is_truthy

from RADKit.base import RADKitLibraryError

if typing.TYPE_CHECKING:
    from typing import Any


class ExecutionKeywords:
    """Keywords for executing commands on RADKit devices."""

    @staticmethod
    def _extract_results(
        command: str | list[str], result: Any
    ) -> tuple[dict[str, Any], int, int]:
        """Extract results from a RADKit exec response."""
        results: dict[str, Any] = {}
        single_command = isinstance(command, str)
        success = errors = 0
        for device in result.full_result:
            if single_command:
                try:
                    results[device] = result.full_result[device][command].data
                    success += 1
                except radkit_client.sync.exceptions.ClientError:
                    results[device] = None
                    errors += 1
            else:
                results[device] = {}
                for cmd in command:
                    try:
                        results[device][cmd] = result.full_result[device][cmd].data
                        success += 1
                    except radkit_client.sync.exceptions.ClientError:
                        results[device][cmd] = None
                        errors += 1
        return results, success, errors

    @keyword("RADKit Execute")
    def radkit_execute_sync(
        self,
        commands: str | list[str],
        devices: Any = None,
        exec_timeout: int | str | None = None,
        raw: bool = False,
    ) -> Any:
        """<p>Execute one or more commands on one or more RADKit devices from the
            currently selected remote RADKit service instance.</p>

            <p>The execution is synchronous — the keyword waits until all commands
            are executed.</p>

            <p>Commands can be passed as a string (single command) or a list of strings
            (multiple commands). Devices can be a semicolon-separated string, a list,
            or a RADKit DeviceDict. If devices is not provided, the previously selected
            devices are used.</p>

            <p>For a single command, the result dict maps device names to output strings.
            For multiple commands, the result is a dict of dicts:
            <code>result[device][command]</code>.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>commands</code>: Command or list of commands to execute</li>
                <li><code>devices</code>: Device(s) to execute on (optional)</li>
                <li><code>exec_timeout</code>: Execution timeout in seconds
                    (optional)</li>
                <li><code>raw</code>: Return raw RADKit response type (optional,
                    default False)</li>
            </ul>

            <p><strong>Returns:</strong> Dict of command output per device</p>

            <p><strong>Example:</strong></p>
            <pre>
        RADKit Select Service    1111-2222-3333
        @{devices}=    Create List    router1    router2    router3
        ${result}=    RADKit Execute    show version    devices=${devices}
        # output: ${result}[router1], ${result}[router2], etc.

        @{commands}=    Create List    show version    show clock
        ${result}=    RADKit Execute    ${commands}    devices=router1;router2
        # output: ${result}[router1][show version], etc.
            </pre>
        """
        devices = self._get_devices(devices)  # type: ignore[attr-defined]
        exec_timeout_int = self._get_timeout(exec_timeout)  # type: ignore[attr-defined]
        result = devices.exec(commands, timeout=exec_timeout_int).wait()
        if is_truthy(raw):
            res, _, _ = self._extract_results(commands, result)
            logger.info(f"result: {res}")
            return result
        else:
            results, success, errors = self._extract_results(commands, result)
            if success == 0:
                raise RADKitLibraryError("No command was successfully executed")
            if errors:
                logger.warn("Some errors occurred collecting the commands")
            return results
