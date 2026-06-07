import shlex
from typing import Optional

from k8s_cluster.commands.infra.constants import (
    CLUSTER_HELM_RELEASES,
    COMPOSE_DIR,
    COMPOSE_SERVICES,
    DEFAULT_CLUSTER_DROP_ORDER,
    DEFAULT_COMPOSE_DROP_ORDER,
)
from k8s_cluster.commands.infra.types import DropInfraRequest, DropMode, InfraService
from k8s_cluster.services.helm import helm_uninstall
from k8s_cluster.utils.compose_runner import execute_cli_command_in_dir
from k8s_cluster.utils.shell import execute_cli_command


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


def drop_cluster(namespace: str, services: list[str]) -> int:
    exit_code = 0
    for service in services:
        release = CLUSTER_HELM_RELEASES[service]
        exit_code += helm_uninstall(release, namespace)

    if exit_code == 0:
        print(f'Infra release(s) removed from namespace "{namespace}": {", ".join(services)}.')
    return 0 if exit_code == 0 else 1


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


def drop_infra(request: DropInfraRequest) -> int:
    services = resolve_services(request.services, request.mode)
    if request.mode == DropMode.cluster:
        return drop_cluster(request.namespace, services)
    return drop_compose(services, request.remove_volumes)
