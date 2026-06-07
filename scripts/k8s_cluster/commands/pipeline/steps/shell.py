import os

from k8s_cluster.commands.pipeline.log import log_step_detail
from k8s_cluster.utils.docker import docker_desktop_env_prefix, is_minikube_docker_env
from k8s_cluster.utils.shell import execute_cli_command


def write_secrets_to_file(secrets: dict, output_file: str):
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w") as file:
        for key, value in secrets.items():
            file.write(f"{key}={value}\n")


def prepare_shell_command(cmd: str, step_name: str) -> str:
    if step_name == "test" and is_minikube_docker_env():
        log_step_detail("Using Docker Desktop for test step (minikube docker-env detected)")
        return docker_desktop_env_prefix() + cmd
    return cmd


def run_shell_step(cmd: str, step_name: str) -> int:
    return execute_cli_command(prepare_shell_command(cmd, step_name))
