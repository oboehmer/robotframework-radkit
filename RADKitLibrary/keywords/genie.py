# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Genie-related keywords for RADKit Robot Framework library."""

from __future__ import annotations

import typing

import radkit_client.sync
from robot.api.deco import keyword
from robot.utils import is_truthy

from ..base import RADKitLibraryError

if typing.TYPE_CHECKING:
    from typing import Any

try:
    import radkit_genie
except ImportError:
    radkit_genie = None  # type: ignore[assignment]

_GENIE_INSTALL_MSG = (
    "cisco-radkit-genie is required for Genie keywords. "
    "Install with: pip install robotframework-radkit[genie]"
)


def _require_genie() -> None:
    """Raise RADKitLibraryError if radkit_genie is not installed."""
    if radkit_genie is None:
        raise RADKitLibraryError(_GENIE_INSTALL_MSG)


class GenieKeywords:
    """Keywords for RADKit Genie parsing, learning, and fingerprinting."""

    @keyword("RADKit Genie Parse")
    def radkit_genie_parse(
        self,
        commands: str | list[str] | None = None,
        devices: Any = None,
        os: str | None = None,
        exec_timeout: int | str | None = None,
        raw_output: Any = None,
    ) -> Any:
        """<p>Parse command output from one or more devices using Genie parsers.</p>

            <p>Either provide <code>commands</code> and <code>devices</code> to execute
            and parse in one step, or provide <code>raw_output</code> from a previous
            <code>RADKit Execute</code> call (with <code>raw=True</code>).</p>

            <p>The device's operating system can be provided via <code>os</code>, or
            auto-detected using <code>RADKit Genie Fingerprint</code> beforehand.</p>

            <p>Returns a dictionary with structure
            <code>[device][command]</code>.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>commands</code>: Command(s) to execute and parse</li>
                <li><code>devices</code>: Device(s) to execute on</li>
                <li><code>os</code>: Device OS (e.g. iosxe, iosxr)</li>
                <li><code>exec_timeout</code>: Execution timeout (optional)</li>
                <li><code>raw_output</code>: Raw result from RADKit Execute
                    (alternative to commands/devices)</li>
            </ul>

            <p><strong>Returns:</strong> Parsed result dictionary (QDict)</p>

            <p><strong>Example:</strong></p>
            <pre>
        RADKit Select Service    1111-2222-3333
        @{devices}=    Create List    router1    router2
        ${result}=    RADKit Genie Parse    commands=show version
        ...    devices=${devices}    os=iosxe
            </pre>
        """
        _require_genie()

        if commands is not None and raw_output is not None:
            raise ValueError(
                "either pass commands and devices OR the raw output from a previous "
                "RADKit Execute command, but not both"
            )

        if raw_output is None:
            result = self.radkit_execute_sync(  # type: ignore[attr-defined]
                commands=commands,
                devices=devices,
                exec_timeout=exec_timeout,
                raw=True,
            )
        else:
            if not isinstance(raw_output, radkit_client.sync.ExecResponseBase):
                raise ValueError(
                    "expected argument is not a raw RADKit result, please use "
                    "the raw=True argument to RADKit Execute keyword"
                )
            result = raw_output

        parsed_result = radkit_genie.parse(result, os=os)
        return radkit_genie.parsed_to_dict(parsed_result)

    @keyword("RADKit Genie Learn")
    def radkit_genie_learn(
        self,
        models: str | list[str],
        devices: Any = None,
        os: str | None = None,
        exec_timeout: int | str | None = None,
        skip_unknown_os: bool = False,
    ) -> Any:
        """<p>Use Genie's <code>learn</code> method to parse device features
            (models) into structured data.</p>

            <p>Returns a dictionary with structure
            <code>[device][model]</code>.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>models</code>: Model or list of models (e.g. routing,
                    platform)</li>
                <li><code>devices</code>: Device(s) to learn from</li>
                <li><code>os</code>: Device OS (e.g. iosxe, iosxr)</li>
                <li><code>exec_timeout</code>: Execution timeout (optional)</li>
                <li><code>skip_unknown_os</code>: Skip devices with unknown OS
                    (default False)</li>
            </ul>

            <p><strong>Returns:</strong> Parsed result dictionary (QDict)</p>

            <p><strong>Example:</strong></p>
            <pre>
        RADKit Select Service    1111-2222-3333
        @{devices}=    Create List    router1    router2
        ${result}=    RADKit Genie Learn    platform
        ...    devices=${devices}    os=iosxe
            </pre>
        """
        _require_genie()

        devices = self._get_devices(devices)  # type: ignore[attr-defined]
        if isinstance(models, str):
            models = [models]
        elif isinstance(models, list):
            pass
        else:
            raise ValueError("expected a single model (string) or a list of models")
        skip_unknown_os_bool = is_truthy(skip_unknown_os)
        exec_timeout_int = self._get_timeout(exec_timeout)  # type: ignore[attr-defined]
        parsed_result = radkit_genie.learn(
            devices,
            models,
            os=os,
            exec_timeout=exec_timeout_int,
            skip_unknown_os=skip_unknown_os_bool,
        )
        return parsed_result.to_dict()

    @keyword("RADKit Genie Fingerprint")
    def radkit_genie_fingerprint(
        self,
        devices: Any,
        exec_timeout: int | str | None = None,
    ) -> Any:
        """<p>Auto-detect the operating system of RADKit devices.</p>

            <p>Once fingerprinted, subsequent Genie Parse and Learn calls no longer
            require the <code>os</code> argument for those devices.</p>

            <p><strong>Arguments:</strong></p>
            <ul>
                <li><code>devices</code>: Device(s) to fingerprint</li>
                <li><code>exec_timeout</code>: Execution timeout (optional)</li>
            </ul>

            <p><strong>Returns:</strong> Dict mapping device names to detected OS</p>

            <p><strong>Example:</strong></p>
            <pre>
        RADKit Select Service    1111-2222-3333
        @{devices}=    Create List    router1    router2
        RADKit Genie Fingerprint    ${devices}
        # Now Parse and Learn no longer require the os argument
        ${parsed}=    RADKit Genie Parse    commands=show version
        ...    devices=${devices}
            </pre>
        """
        _require_genie()

        devices = self._get_devices(devices)  # type: ignore[attr-defined]
        exec_timeout_int = self._get_timeout(exec_timeout)  # type: ignore[attr-defined]
        return radkit_genie.fingerprint(devices, exec_timeout=exec_timeout_int)
