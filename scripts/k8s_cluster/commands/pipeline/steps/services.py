import os
import shlex
import time

from k8s_cluster.commands.pipeline.log import log_step_detail
from k8s_cluster.commands.pipeline.steps.shell import write_secrets_to_file
from k8s_cluster.commands.pipeline.types import ServiceArgs
from k8s_cluster.utils.shell import execute_cli_command


def wait_for_docker_postgres(container_id: str, pg_user: str, timeout_seconds: int = 60) -> int:
    for second in range(timeout_seconds):
        exit_code = execute_cli_command(
            f"docker exec {shlex.quote(container_id)} " f"pg_isready -U {shlex.quote(pg_user)} -q"
        )
        if exit_code == 0:
            if second > 0:
                log_step_detail(f"PostgreSQL ready after {second + 1}s")
            return 0
        time.sleep(1)

    log_step_detail(f'PostgreSQL in container "{container_id}" did not become ready within {timeout_seconds}s')
    return 1


def handle_service(service_name: str, repository: str, args: ServiceArgs, temp_folder_path: str):
    container_id = f"{repository}-{service_name}"
    log_step_detail(f"Starting container {container_id} (image {args.image}, ports {args.image_port_map})")
    image_env_vars = " ".join(
        [f"-e {key}={value}" for key, value in args.image_env_vars.items()],
    )
    credentials_path = os.path.join(temp_folder_path, args.output_file.lstrip("./"))
    write_secrets_to_file(args.env_vars, credentials_path)
    log_step_detail(f"Writing service env to {credentials_path}")

    execute_cli_command(f"docker rm -f {container_id} >/dev/null 2>&1")

    exit_code = execute_cli_command(
        "docker run --pull=always -d " f"--name {container_id} -p {args.image_port_map} {image_env_vars} {args.image}"
    )
    if exit_code != 0:
        return container_id, exit_code

    pg_user = args.image_env_vars.get("POSTGRES_USER", "postgres")
    return container_id, wait_for_docker_postgres(container_id, pg_user)
