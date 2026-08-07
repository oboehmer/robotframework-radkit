# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Pytest wrapper for Robot Framework smoke tests.

This script ensures the required dependencies (unicon, pyats.robot) are installed
with the same major version as the currently installed genie package, verifies
that required environment variables are set, and then invokes test_smoke.robot.

Can be run directly: python tests/smoke/test_smoke.py
Or via pytest:      pytest tests/smoke/test_smoke.py
"""

import os
import subprocess
import sys
from base64 import b64encode
from importlib.metadata import version as pkg_version
from pathlib import Path

from robot import run_cli  # type: ignore[attr-defined]

REQUIRED_ENV_VARS = ("RADKIT_IDENTITY", "RADKIT_CLIENT_PRIVATE_KEY_PASSWORD")
ROBOT_FILE = Path(__file__).parent / "test_smoke.robot"
ROBOT_OUTPUT_DIR = Path(__file__).parent / "robot_output"


def _get_genie_major_version() -> str:
    """Return the major version of the installed genie package.

    Exits with an error if genie is not installed.
    """
    try:
        genie_version = pkg_version("genie")
    except Exception:
        sys.exit(
            "ERROR: The 'genie' package is not installed.\n"
            "Install it via the genie extra dependency, e.g.:\n"
            "  pip install robotframework-radkit[genie]\n"
            "  uv pip install robotframework-radkit[genie]"
        )
    major = genie_version.split(".")[0]
    return major


def _ensure_dependencies_installed(major_version: str) -> None:
    """Install unicon and pyats.robot matching the genie major version."""
    packages = [
        f"unicon~={major_version}.0",
        f"pyats.robot~={major_version}.0",
    ]
    print(f"Ensuring dependencies are installed: {packages}")
    subprocess.check_call(
        ["uv", "pip", "install", *packages],
        stdout=subprocess.DEVNULL,
    )


def _check_environment() -> None:
    """Verify required environment variables are set and derive additional ones."""
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        sys.exit(
            "ERROR: Required environment variables are not set:\n"
            + "\n".join(f"  - {var}" for var in missing)
        )
    # Set base64-encoded password for tests that need it
    password = os.environ["RADKIT_CLIENT_PRIVATE_KEY_PASSWORD"]
    os.environ["RADKIT_CLIENT_PRIVATE_KEY_PASSWORD_BASE64"] = b64encode(
        password.encode()
    ).decode()


def _run_robot(extra_args: list[str] | None = None) -> int:
    """Run the Robot Framework smoke test suite. Returns the exit code."""
    args = [
        "--outputdir",
        str(ROBOT_OUTPUT_DIR),
        "--loglevel",
        "TRACE",
    ]
    if extra_args:
        args.extend(extra_args)
    args.append(str(ROBOT_FILE))
    rc: int = run_cli(args, exit=False)
    return rc


def setup_module() -> None:
    """Pytest module-level setup: install deps and check env."""
    major = _get_genie_major_version()
    _ensure_dependencies_installed(major)
    _check_environment()


def test_smoke() -> None:
    """Run the Robot Framework smoke test suite."""
    rc = _run_robot()
    assert rc == 0, f"Robot Framework smoke tests failed with exit code {rc}"


if __name__ == "__main__":
    setup_module()
    sys.exit(_run_robot(sys.argv[1:]))
