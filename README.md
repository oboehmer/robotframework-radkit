# Robot Framework RADKit Library

A Robot Framework library for interacting with Cisco [RADKit](https://radkit.cisco.com/)-connected devices, providing keywords for authentication, device inventory, parallel command execution, port forwarding, and Genie-based structured parsing.

[![Python versions](https://img.shields.io/pypi/pyversions/robotframework-radkit.svg)](https://pypi.org/project/robotframework-radkit/)
[![License](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

## Installation

RADKit client packages are hosted on a Cisco-internal PyPI index. Configure pip accordingly:

```bash
pip install --extra-index-url https://radkit.cisco.com/pip robotframework-radkit
```

For Genie parsing support (optional):

```bash
pip install --extra-index-url https://radkit.cisco.com/pip robotframework-radkit[genie]
```

## Prerequisites

- Python 3.10+
- A RADKit identity with enrolled certificates (see [RADKit documentation](https://radkit.cisco.com/docs/))
- Access to a RADKit service (remote service instance)

## Quick Start

```robot
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
```

## Keywords

### Connection Management

| Keyword | Description |
|---------|-------------|
| `RADKit Client Version` | Return installed radkit_client version |
| `RADKit certificate login` | Authenticate to RADKit cloud via certificates |
| `RADKit disconnect` | Disconnect from RADKit cloud (all or specific identity) |
| `RADKit select service` | Connect to a RADKit service by serial |
| `RADKit timeout` | Set execution timeout (default: 300s) |

### Device Management

| Keyword | Description |
|---------|-------------|
| `RADKit device inventory` | Retrieve device inventory (with optional filter) |
| `RADKit select devices` | Select default devices for subsequent execute calls |

### Command Execution

| Keyword | Description |
|---------|-------------|
| `RADKit execute` | Execute CLI commands on one or more devices in parallel |

### Port Forwarding

| Keyword | Description |
|---------|-------------|
| `RADKit Port Forward to Device` | Set up TCP port forwarding to a remote device |
| `RADKit Stop Port Forward` | Stop an active port forwarder |

### Genie Parsing (optional, requires `robotframework-radkit[genie]`)

| Keyword | Description |
|---------|-------------|
| `RADKit Genie Parse` | Parse command output using Genie parsers |
| `RADKit Genie Learn` | Learn device models (structured data) via Genie |
| `RADKit Genie Fingerprint` | Auto-detect device OS for subsequent Genie operations |

## Authentication

The library uses certificate-based authentication. Credentials can be provided as keyword arguments or through environment variables:

| Environment Variable | Description |
|---------------------|-------------|
| `RADKIT_IDENTITY` | Your Cisco email address |
| `RADKIT_CERT_PATH` | Path to your RADKit certificate |
| `RADKIT_KEY_PATH` | Path to your private key |
| `RADKIT_CA_PATH` | Path to CA certificate chain |
| `RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64` | Base64-encoded private key passphrase |
| `RADKIT_CLIENT_PRIVATE_KEY_PASSWORD` | Cleartext private key passphrase |

## Optional pyATS Integration

When `pyats.robot.pyATSRobot` is loaded in the test suite, the `RADKit Port Forward to Device` keyword can optionally update testbed device connection entries via the `testbed_device` and `testbed_conn` parameters. This feature is automatically available when pyATS is installed; no additional configuration is needed.

```robot
*** Settings ***
Library    pyats.robot.pyATSRobot
Library    RADKit

*** Test Cases ***
Port Forward With Testbed Update
    RADKit certificate login    identity=user@cisco.com
    RADKit select service    ${SERVICE_SN}
    RADKit Port Forward to Device    linuxdevice    local_port=0
    ...    destination_port=22    testbed_device=linux_server    testbed_conn=cli
    connect to device "linux_server" via "cli"
```

## Usage Examples

### Execute Commands on Multiple Devices

```robot
RADKit select service    ${SERVICE_SN}
@{devices}=    Create List    router1    router2    router3
${result}=    RADKit execute    show version    devices=${devices}
# Access output: ${result}[router1], ${result}[router2], etc.
```

### Execute Multiple Commands

```robot
@{commands}=    Create List    show version    show clock
${result}=    RADKit execute    ${commands}    devices=router1;router2
# Access: ${result}[router1][show version], ${result}[router1][show clock], etc.
```

### Use Inventory Filters

```robot
${inventory}=    RADKit device inventory    raw=True
${subset}=    Evaluate    $inventory.filter("name", "PE*").filter("device_type", "IOSXE")
${result}=    RADKit execute    show version    devices=${subset}
```

### Parse Output with Genie

```robot
@{devices}=    Create List    router1    router2
RADKit Genie Fingerprint    ${devices}
${parsed}=    RADKit Genie Parse    commands=show version    devices=${devices}
# Access parsed data: ${parsed}[router1][show version][version]
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/oboehmer/robotframework-radkit.git
cd robotframework-radkit

# Install in development mode (requires access to radkit.cisco.com/pip)
pip install --extra-index-url https://radkit.cisco.com/pip -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/test_unit_*.py

# Run with coverage
pytest --cov=RADKit tests/

# Run linters
ruff check .
mypy .
bandit -r RADKit/
```

### Code Quality

This project uses:
- **ruff** for linting and formatting
- **mypy** for type checking
- **bandit** for security analysis
- **pytest** for testing
- **pre-commit** for git hooks

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## Resources

- [RADKit Website](https://radkit.cisco.com/)
- [RADKit Documentation](https://radkit.cisco.com/docs/)
- [Robot Framework Documentation](https://robotframework.org/)

## License

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](LICENSE) file for details.

## Authors

- Oliver Boehmer ([@oboehmer](https://github.com/oboehmer))
