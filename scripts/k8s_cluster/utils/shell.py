import os


def execute_cli_command(command: str) -> int:
    print(f"Executing command: {command}")
    return os.system(command)
