#!/usr/bin/env python3
"""Run style (black) and lint (flake8) checks for scripts/."""

import subprocess
import sys


def run_step(name: str, command: list[str]) -> int:
    print(f"Running {name}...")
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f"{name} failed with exit code {result.returncode}")
    return result.returncode


def main() -> int:
    steps = [
        ("black", [sys.executable, "-m", "black", "--check", "."]),
        ("flake8", [sys.executable, "-m", "flake8", "."]),
    ]
    for name, command in steps:
        exit_code = run_step(name, command)
        if exit_code != 0:
            return exit_code
    print("codeChecks passed (black + flake8)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
