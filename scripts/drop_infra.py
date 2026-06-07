import os
import shlex
from enum import Enum
from typing import Optional

import typer

from cli_common import exit_on_failure, make_cli_app
from infra_common import execute_cli_command
from repo_paths import REPO_ROOT

app = make_cli_app()

INFRA_DIR = os.path.join(REPO_ROOT, "apps", "infra")
COMPOSE_DIR = INFRA_DIR

DEFAULT_CLUSTER_DROP_ORDER = [
    "kafka-ui",
    "localstack",
    "kafka",
    "postgresql",
]

DEFAULT_COMPOSE_DROP_ORDER = [
    "localstack",
    "kafka",
    "postgresql",
]

CLUSTER_HELM_RELEASES = {
    "postgresql": "postgresql",
    "kafka": "kafka",
    "localstack": "localstack",
    "kafka-ui": "kafka-ui",
}

COMPOSE_SERVICES = {
    "postgresql": "postgres",
    "kafka": "kafka",
    "localstack": "localstack",
}


class DropMode(str, Enum):
    cluster = "cluster"
    compose = "compose"


class InfraService(str, Enum):
    postgresql = "postgresql"
    kafka = "kafka"
    localstack = "localstack"
    kafka_ui = "kafka-ui"


def resolve_services(services: Optional[list[InfraService]], mode: DropMode) -> list[str]:
    if not services:
        if mode == DropMode.compose:
            return list(DEFAULT_COMPOSE_DROP_ORDER)
        return list(DEFAULT_CLUSTER_DROP_ORDER)

    selected = []
    seen = set()
    for service in services:
        name = service.value
        if name in seen:
            continue
        seen.add(name)
        selected.append(name)
    return selected


def helm_uninstall(release: str, namespace: str) -> int:
    print(f'Uninstalling Helm release "{release}" from namespace "{namespace}"...')
    return execute_cli_command(f"helm uninstall {shlex.quote(release)} -n {shlex.quote(namespace)} --ignore-not-found")


def drop_cluster(namespace: str, services: list[str]) -> int:
    exit_code = 0
    for service in services:
        release = CLUSTER_HELM_RELEASES[service]
        exit_code += helm_uninstall(release, namespace)

    if exit_code == 0:
        print(f'Infra release(s) removed from namespace "{namespace}": {", ".join(services)}.')
    return 0 if exit_code == 0 else 1


def execute_cli_command_in_dir(command: str, cwd: str) -> int:
    print(f"Executing command in {cwd}: {command}")
    previous_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        return os.system(command)
    finally:
        os.chdir(previous_cwd)


def drop_compose(services: list[str], remove_volumes: bool) -> int:
    exit_code = execute_cli_command("docker version")
    if exit_code != 0:
        print("docker is not available.")
        return exit_code

    exit_code = execute_cli_command("docker compose version")
    if exit_code != 0:
        print("docker compose is not available.")
        return exit_code

    unsupported = [service for service in services if service not in COMPOSE_SERVICES]
    if unsupported:
        names = ", ".join(unsupported)
        print(f"Compose mode does not support: {names}. Available: postgresql, kafka, localstack.")
        return 1

    compose_services = [COMPOSE_SERVICES[service] for service in services]
    service_args = " ".join(shlex.quote(name) for name in compose_services)
    rm_flags = "-sf"
    if remove_volumes:
        rm_flags = "-sfv"

    print(f'Stopping Compose infra service(s): {", ".join(compose_services)}...')
    exit_code = execute_cli_command_in_dir(f"docker compose stop {service_args}", COMPOSE_DIR)
    if exit_code != 0:
        return exit_code

    exit_code = execute_cli_command_in_dir(f"docker compose rm {rm_flags} {service_args}", COMPOSE_DIR)
    if exit_code == 0:
        print(f'Compose infra stopped: {", ".join(compose_services)}.')
    return exit_code


@app.command()
def cli(
    mode: DropMode = typer.Option(
        DropMode.cluster,
        "--mode",
        help="cluster (Helm uninstall) or compose (docker compose stop/rm from apps/infra)",
    ),
    namespace: str = typer.Option("dev", help="Kubernetes namespace (cluster mode only)"),
    volumes: bool = typer.Option(
        False,
        "--volumes",
        help="Compose mode only: remove named volumes for selected service(s)",
    ),
    service: Optional[list[InfraService]] = typer.Option(
        None,
        "--service",
        "-s",
        help="Infra to remove (repeatable): postgresql, kafka, localstack, kafka-ui. Default: all",
    ),
) -> None:
    services = resolve_services(service, mode)

    if mode == DropMode.cluster:
        if volumes:
            typer.echo("--volumes applies to compose mode only.", err=True)
            raise typer.Exit(code=1)
        exit_code = drop_cluster(namespace, services)
    else:
        exit_code = drop_compose(services, volumes)

    exit_on_failure(exit_code, "")


if __name__ == "__main__":
    app()
