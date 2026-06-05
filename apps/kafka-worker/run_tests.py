#!/usr/bin/env python3
"""Run Django tests with coverage report, verification, and HTML/XML output."""

import os
import subprocess
import sys


def run_step(name: str, command: list[str], env: dict | None = None) -> int:
    print(f'Running {name}...')
    result = subprocess.run(command, check=False, env=env)
    if result.returncode != 0:
        print(f'{name} failed with exit code {result.returncode}')
    return result.returncode


def main() -> int:
    test_env = os.environ.copy()
    test_env.setdefault('PYTHONWARNINGS', 'default')

    steps = [
        (
            'coverage run',
            [sys.executable, '-m', 'coverage', 'run', 'manage.py', 'test', 'kafkaworker.tests'],
            test_env,
        ),
        ('coverage report', [sys.executable, '-m', 'coverage', 'report'], None),
        ('coverage html', [sys.executable, '-m', 'coverage', 'html'], None),
        ('coverage xml', [sys.executable, '-m', 'coverage', 'xml'], None),
    ]
    for name, command, env in steps:
        exit_code = run_step(name, command, env)
        if exit_code != 0:
            return exit_code
    print('Tests passed with coverage report at reports/coverage/html/index.html')
    return 0


if __name__ == '__main__':
    sys.exit(main())
