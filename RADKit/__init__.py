# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""
RADKit library for Robot Framework.

This library provides keywords for interacting with Cisco RADKit-connected
devices, including authentication, device inventory, command execution,
port forwarding, and Genie-based parsing.
"""

from RADKit._base import BaseMixin, RADKitLibraryError
from RADKit.keywords import (
    ConnectionKeywords,
    DirectKeywords,
    ExecutionKeywords,
    GenieKeywords,
    InventoryKeywords,
    PortForwardingKeywords,
)

__version__ = "0.1.0"
__all__ = ["RADKit", "RADKitLibraryError"]


class RADKit(
    BaseMixin,
    ConnectionKeywords,
    DirectKeywords,
    InventoryKeywords,
    ExecutionKeywords,
    PortForwardingKeywords,
    GenieKeywords,
):
    """<p>RADKit is a Robot Framework library for interacting with Cisco
    <a href="https://radkit.cisco.com/">RADKit</a>-connected devices.</p>

    <p>It provides keywords for authenticating to RADKit cloud, querying device
    inventories, executing CLI commands across multiple devices in parallel,
    setting up TCP port forwarding, and leveraging Genie parsers for structured
    output.</p>

    <h2>Installation</h2>

    <p>RADKit client packages are hosted on a Cisco-internal PyPI index.
    Configure pip accordingly:</p>

    <pre>
    pip install --extra-index-url https://radkit.cisco.com/pip robotframework-radkit
    </pre>

    <p>For Genie parsing support:</p>
    <pre>
    pip install --extra-index-url https://radkit.cisco.com/pip robotframework-radkit[genie]
    </pre>

    <h2>Prerequisites</h2>

    <ul>
        <li>A RADKit identity with enrolled certificates
            (see <a href="https://radkit.cisco.com/docs/">RADKit documentation</a>)</li>
        <li>Access to a RADKit service (remote service instance)</li>
    </ul>

    <h2>Quick Start</h2>

    <pre>
    *** Settings ***
    Library    RADKit

    *** Variables ***
    ${SERVICE_SN}    abcd-1234-efgh

    *** Test Cases ***
    Query Device Inventory
        # identity can also be set via RADKIT_IDENTITY env var
        RADKit certificate login    identity=user@cisco.com
        RADKit select service    ${SERVICE_SN}
        @{devices}=    RADKit device inventory
        Log Many    @{devices}

    Execute Show Version
        RADKit certificate login    identity=user@cisco.com
        RADKit select service    ${SERVICE_SN}
        ${result}=    RADKit execute    show version    devices=router1
        Log    ${result}[router1]
    </pre>

    <h2>Authentication</h2>

    <p>The library uses certificate-based authentication. Certificates and identity
    can be provided as keyword arguments or through environment variables:</p>

    <table border="1">
        <tr>
            <th>Environment Variable</th>
            <th>Description</th>
        </tr>
        <tr>
            <td><code>RADKIT_IDENTITY</code></td>
            <td>Your Cisco email address</td>
        </tr>
        <tr>
            <td><code>RADKIT_CERT_PATH</code></td>
            <td>Path to your RADKit certificate</td>
        </tr>
        <tr>
            <td><code>RADKIT_KEY_PATH</code></td>
            <td>Path to your private key</td>
        </tr>
        <tr>
            <td><code>RADKIT_CA_PATH</code></td>
            <td>Path to CA certificate chain</td>
        </tr>
        <tr>
            <td><code>RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64</code></td>
            <td>Base64-encoded private key passphrase</td>
        </tr>
        <tr>
            <td><code>RADKIT_CLIENT_PRIVATE_KEY_PASSWORD</code></td>
            <td>Cleartext private key passphrase</td>
        </tr>
    </table>

    <h2>Optional pyATS Integration</h2>

    <p>When <code>pyats.robot.pyATSRobot</code> is loaded in the test suite,
    the port forwarding keyword can optionally update testbed device connection
    entries. This feature is automatically available when pyATS is installed;
    no additional configuration is needed.</p>

    <h2>Optional Genie Support</h2>

    <p>The Genie keywords (Parse, Learn, Fingerprint) require the
    <code>cisco-radkit-genie</code> package. Install with:</p>
    <pre>pip install robotframework-radkit[genie]</pre>

    <h2>Keywords</h2>

    <h3>Connection Management</h3>
    <ul>
        <li><code>RADKit Client Version</code> - Return installed radkit_client version</li>
        <li><code>RADKit certificate login</code> - Authenticate to RADKit cloud</li>
        <li><code>RADKit disconnect</code> - Disconnect from RADKit cloud</li>
        <li><code>RADKit select service</code> - Connect to a RADKit service</li>
        <li><code>RADKit service direct</code> - Connect directly to a RADKit service via host/port</li>
        <li><code>RADKit disconnect direct service</code> - Disconnect direct service connections</li>
        <li><code>RADKit timeout</code> - Set execution timeout</li>
    </ul>

    <h3>Device Management</h3>
    <ul>
        <li><code>RADKit device inventory</code> - Retrieve device inventory</li>
        <li><code>RADKit select devices</code> - Select default devices</li>
    </ul>

    <h3>Command Execution</h3>
    <ul>
        <li><code>RADKit execute</code> - Execute CLI commands on devices</li>
    </ul>

    <h3>Port Forwarding</h3>
    <ul>
        <li><code>RADKit Port Forward to Device</code> - Set up TCP port forwarding</li>
        <li><code>RADKit Stop Port Forward</code> - Stop port forwarding</li>
    </ul>

    <h3>Genie Parsing (optional)</h3>
    <ul>
        <li><code>RADKit Genie Parse</code> - Parse command output with Genie</li>
        <li><code>RADKit Genie Learn</code> - Learn device models with Genie</li>
        <li><code>RADKit Genie Fingerprint</code> - Auto-detect device OS</li>
    </ul>

    <h2>Resources</h2>

    <ul>
        <li><a href="https://radkit.cisco.com/">RADKit Website</a></li>
        <li><a href="https://radkit.cisco.com/docs/">RADKit Documentation</a></li>
        <li><a href="https://robotframework.org/">Robot Framework Documentation</a></li>
        <li><a href="https://github.com/oboehmer/robotframework-radkit">GitHub Repository</a></li>
    </ul>
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_DOC_FORMAT = "HTML"
    __version__ = __version__
