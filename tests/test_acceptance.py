# SPDX-License-Identifier: MPL-2.0
# Copyright (c) 2025 Oliver Boehmer

"""Pytest wrapper for Robot Framework acceptance tests."""

from pathlib import Path

from robot import run  # type: ignore[attr-defined]


def test_robot_acceptance_tests() -> None:
    """Run Robot Framework acceptance tests and verify they pass."""
    test_dir = Path(__file__).parent
    robot_file = test_dir / "acceptance.robot"

    # Run robot tests with minimal output
    result = run(
        str(robot_file),
        outputdir=str(test_dir / "robot_output"),
        loglevel="INFO",
    )

    # Assert all tests passed (return code 0)
    assert result == 0, f"Robot Framework tests failed with return code: {result}"
