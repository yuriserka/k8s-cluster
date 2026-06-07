import os

from k8s_cluster.utils.shell import execute_cli_command


def execute_cli_command_in_dir(command: str, cwd: str) -> int:
    print(f"Executing command in {cwd}: {command}")
    previous_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        return execute_cli_command(command)
    finally:
        os.chdir(previous_cwd)
