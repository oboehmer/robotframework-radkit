# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-04-10

### Added
- Initial release
- `RADKit Client Version` keyword to report installed version
- `RADKit certificate login` keyword for certificate-based authentication
- `RADKit disconnect` keyword for connection teardown
- `RADKit select service` keyword for service selection
- `RADKit timeout` keyword for execution timeout configuration
- `RADKit device inventory` keyword with filtering and raw output support
- `RADKit select devices` keyword for default device selection
- `RADKit execute` keyword for parallel command execution across devices
- `RADKit Port Forward to Device` keyword with optional pyATS testbed integration
- `RADKit Stop Port Forward` keyword
- `RADKit Genie Parse` keyword for structured output parsing (optional dependency)
- `RADKit Genie Learn` keyword for Genie model learning (optional dependency)
- `RADKit Genie Fingerprint` keyword for OS auto-detection (optional dependency)
- Optional pyATS testbed integration for port forwarding
- Python 3.10+ support
- Type hints and mypy validation
- Comprehensive test suite
- GitHub Actions CI/CD

[0.1.0]: https://github.com/oboehmer/robotframework-radkit/releases/tag/v0.1.0
