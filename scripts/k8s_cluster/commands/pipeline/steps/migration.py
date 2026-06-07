import json
import os
import shlex
from datetime import datetime

from k8s_cluster.commands.database.service import create_database
from k8s_cluster.commands.database.types import CreateDatabaseRequest
from k8s_cluster.commands.pipeline.log import log_step_detail
from k8s_cluster.commands.pipeline.types import DatabaseMigrationStepArgs
from k8s_cluster.paths import REPO_ROOT
from k8s_cluster.services.kubectl import delete_pod, get_pod, get_pod_container_exit_code
from k8s_cluster.services.pod_wait import (
    DEFAULT_POSTGRES_SERVICE,
    READY_TIMEOUT_SECONDS,
    wait_for_pod,
    wait_for_postgresql_ready,
)
from k8s_cluster.utils.shell import execute_cli_command

DEFAULT_POSTGRES_PORT = "5432"


def read_vault_database_secrets(repository: str, namespace: str) -> dict:
    env_file = os.path.join(REPO_ROOT, "resources", "vault", repository, "database", namespace, ".env")
    secrets = {}
    with open(env_file) as secrets_file:
        for line in secrets_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            secrets[key.upper()] = value.strip()
    return secrets


def resolve_cluster_database_host(namespace: str, secrets: dict) -> str:
    host = secrets.get("CLUSTER_HOST", DEFAULT_POSTGRES_SERVICE)
    exit_code = execute_cli_command(
        "minikube kubectl -- get svc " f"{shlex.quote(host)} -n {shlex.quote(namespace)} >/dev/null 2>&1"
    )
    if exit_code != 0:
        raise RuntimeError(
            f'PostgreSQL service "{host}" not found in namespace "{namespace}". '
            "Install infra (helm postgresql) or set CLUSTER_HOST in vault database .env."
        )
    return host


def load_cluster_database_env(repository: str, namespace: str) -> dict:
    secrets = read_vault_database_secrets(repository, namespace)
    cluster_host = resolve_cluster_database_host(namespace, secrets)

    return {
        "DATABASE_USER": secrets["USER"],
        "DATABASE_PASSWORD": secrets["PASSWORD"],
        "DATABASE_NAME": secrets["NAME"],
        "DATABASE_PORT": secrets.get("PORT", DEFAULT_POSTGRES_PORT),
        "DATABASE_HOST": cluster_host,
    }


def run_in_cluster_migration_command(
    namespace: str,
    image: str,
    env_vars: dict,
    command_argv: list[str],
    run_id: str,
) -> int:
    overrides = {
        "spec": {
            "containers": [
                {
                    "name": "migrate",
                    "image": image,
                    "imagePullPolicy": "Never",
                    "env": [{"name": key, "value": value} for key, value in env_vars.items()],
                    "command": command_argv,
                }
            ],
        },
    }
    pod_name = f"migrate-{run_id}"
    create_cmd = (
        f"minikube kubectl -- run {shlex.quote(pod_name)} "
        f"--restart=Never -n {shlex.quote(namespace)} "
        f"--image={shlex.quote(image)} "
        f"--overrides={shlex.quote(json.dumps(overrides))}"
    )
    exit_code = execute_cli_command(create_cmd)
    if exit_code != 0:
        return exit_code

    exit_code = wait_for_pod(
        pod_name,
        namespace,
        timeout_seconds=READY_TIMEOUT_SECONDS,
        expect_succeeded=True,
        label=pod_name,
    )

    pod = get_pod(pod_name, namespace)
    container_exit_code = get_pod_container_exit_code(pod, "migrate") if pod else 1
    if exit_code != 0 or container_exit_code != 0:
        delete_pod(pod_name, namespace)
        return container_exit_code or exit_code

    delete_pod(pod_name, namespace)
    return 0


def handle_database_migration_step(args: DatabaseMigrationStepArgs, temp_folder_path: str) -> int:
    image = f"{args.image_repo}-{args.env}:{args.env}"
    log_step_detail(f"Database migration for {args.repository} in namespace {args.env}")
    log_step_detail(f"Waiting for {DEFAULT_POSTGRES_SERVICE}-0 in namespace {args.env}")

    exit_code = wait_for_postgresql_ready(args.env)
    if exit_code != 0:
        log_step_detail(
            f"PostgreSQL not ready in namespace {args.env} "
            f"(waited {READY_TIMEOUT_SECONDS}s for pod/{DEFAULT_POSTGRES_SERVICE}-0)"
        )
        return exit_code

    log_step_detail(f"Ensuring database exists for {args.repository}")
    try:
        exit_code = create_database(CreateDatabaseRequest(repository=args.repository, namespace=args.env))
    except (FileNotFoundError, ValueError) as error:
        log_step_detail(str(error))
        return 1
    if exit_code != 0:
        return exit_code

    database_env = load_cluster_database_env(args.repository, args.env)
    run_id = datetime.now().strftime("%H%M%S%f")

    for index, command in enumerate(args.cmd, start=1):
        log_step_detail(f"Running migrate command {index}/{len(args.cmd)}: {command}")
        command_argv = shlex.split(command)
        exit_code = run_in_cluster_migration_command(
            args.env,
            image,
            database_env,
            command_argv,
            f"{run_id}-{index - 1}",
        )
        if exit_code != 0:
            log_step_detail(f"Migrate command {index} failed with exit code {exit_code}")
            return exit_code

    log_step_detail(f"All {len(args.cmd)} migrate command(s) completed successfully")
    return 0
