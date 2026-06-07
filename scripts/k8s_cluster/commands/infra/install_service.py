import os
import shlex
import tempfile
import time

import yaml

from k8s_cluster.commands.infra.constants import (
    COMPOSE_DIR,
    COMPOSE_LOCALSTACK_CONTAINER,
    COMPOSE_POSTGRES_CONTAINER,
    HELM_REPOS,
    INFRA_DIR,
)
from k8s_cluster.commands.infra.types import InstallInfraRequest, InstallMode
from k8s_cluster.paths import REPO_ROOT
from k8s_cluster.services.helm import ensure_helm_repos, helm_upgrade_install
from k8s_cluster.services.pod_wait import (
    READY_TIMEOUT_SECONDS,
    wait_for_kafka_ready,
    wait_for_kafka_ui_ready,
    wait_for_localstack_ready,
    wait_for_postgresql_ready,
)
from k8s_cluster.utils.compose_runner import execute_cli_command_in_dir
from k8s_cluster.utils.env_files import read_env_file
from k8s_cluster.utils.shell import execute_cli_command


def get_localstack_auth_token(namespace: str) -> str:
    env_file = os.path.join(REPO_ROOT, "resources", "vault", "_admin", "aws", namespace, ".env")
    secrets = read_env_file(env_file)
    token = secrets.get("LOCALSTACK_AUTH_TOKEN")
    if not token:
        raise ValueError(
            f"LOCALSTACK_AUTH_TOKEN is missing in {env_file}. " "Copy .env.example and set your LocalStack auth token."
        )
    return token


def ensure_namespace(namespace: str) -> int:
    return execute_cli_command(
        f"minikube kubectl -- create namespace {shlex.quote(namespace)} "
        "--dry-run=client -o yaml | minikube kubectl -- apply -f -"
    )


def build_localstack_values_file(namespace: str) -> str:
    values_path = os.path.join(INFRA_DIR, "localstack", "values.yaml")
    with open(values_path) as values_file:
        values = yaml.safe_load(values_file)

    auth_token = get_localstack_auth_token(namespace)
    values["extraEnvVars"] = [{"name": "LOCALSTACK_AUTH_TOKEN", "value": auth_token}]

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        prefix="localstack-values-",
        delete=False,
    )
    yaml.safe_dump(values, temp_file, sort_keys=False, default_flow_style=None)
    temp_file.close()
    return temp_file.name


def install_cluster_postgresql(namespace: str) -> int:
    values_file = os.path.join(INFRA_DIR, "postgresql", "values.yaml")
    exit_code = helm_upgrade_install("postgresql", "bitnami/postgresql", namespace, values_file)
    if exit_code != 0:
        return exit_code
    return wait_for_postgresql_ready(namespace)


def install_cluster_kafka(namespace: str) -> int:
    values_file = os.path.join(INFRA_DIR, "kafka", "values.yaml")
    exit_code = helm_upgrade_install("kafka", "bitnami/kafka", namespace, values_file)
    if exit_code != 0:
        return exit_code
    return wait_for_kafka_ready(namespace)


def install_cluster_localstack(namespace: str) -> int:
    values_file = build_localstack_values_file(namespace)
    try:
        exit_code = helm_upgrade_install("localstack", "localstack/localstack", namespace, values_file)
        if exit_code != 0:
            return exit_code
        return wait_for_localstack_ready(namespace)
    finally:
        os.remove(values_file)


def install_cluster_kafka_ui(namespace: str) -> int:
    values_file = os.path.join(INFRA_DIR, "kafka-ui", "values.yaml")
    exit_code = helm_upgrade_install("kafka-ui", "kafka-ui/kafka-ui", namespace, values_file)
    if exit_code != 0:
        return exit_code
    return wait_for_kafka_ui_ready(namespace)


def wait_for_compose_container(container_name: str, timeout_seconds: int = READY_TIMEOUT_SECONDS) -> int:
    for second in range(timeout_seconds):
        exit_code = execute_cli_command(
            f"docker inspect -f {shlex.quote('{{.State.Running}}')} "
            f"{shlex.quote(container_name)} 2>/dev/null | grep -q true"
        )
        if exit_code == 0:
            if second > 0:
                print(f'Container "{container_name}" running after {second + 1}s')
            return 0
        time.sleep(1)

    print(f'Container "{container_name}" did not start within {timeout_seconds}s.')
    return 1


def wait_for_compose_postgres(timeout_seconds: int = READY_TIMEOUT_SECONDS) -> int:
    for second in range(timeout_seconds):
        exit_code = execute_cli_command(
            f"docker exec {shlex.quote(COMPOSE_POSTGRES_CONTAINER)} " f"pg_isready -U {shlex.quote('ysdcr')} -q"
        )
        if exit_code == 0:
            if second > 0:
                print(f"PostgreSQL ready after {second + 1}s")
            return 0
        time.sleep(1)

    print(f"PostgreSQL in {COMPOSE_POSTGRES_CONTAINER} did not become ready within {timeout_seconds}s.")
    return 1


def cluster_preflight() -> int:
    exit_code = execute_cli_command("minikube status")
    if exit_code != 0:
        print("minikube is not running. Start it with: minikube start")
        return exit_code

    exit_code = execute_cli_command("helm version")
    if exit_code != 0:
        print("helm is not available.")
    return exit_code


def install_cluster_core_services(namespace: str) -> int:
    for step_name, step in (
        ("PostgreSQL", lambda: install_cluster_postgresql(namespace)),
        ("Kafka", lambda: install_cluster_kafka(namespace)),
        ("LocalStack", lambda: install_cluster_localstack(namespace)),
    ):
        print(f"Installing {step_name}...")
        exit_code = step()
        if exit_code != 0:
            print(f"Failed installing {step_name}.")
            return exit_code
    return 0


def install_cluster(namespace: str, with_kafka_ui: bool) -> int:
    exit_code = cluster_preflight()
    if exit_code != 0:
        return exit_code

    repo_names = ["bitnami", "localstack"]
    if with_kafka_ui:
        repo_names.append("kafka-ui")

    exit_code = ensure_helm_repos(repo_names, HELM_REPOS)
    if exit_code != 0:
        return exit_code

    exit_code = ensure_namespace(namespace)
    if exit_code != 0:
        return exit_code

    exit_code = install_cluster_core_services(namespace)
    if exit_code != 0:
        return exit_code

    if with_kafka_ui:
        print("Installing Kafka UI...")
        exit_code = install_cluster_kafka_ui(namespace)
        if exit_code != 0:
            return exit_code

    print(f'Cluster infra ready in namespace "{namespace}".')
    return 0


def install_compose_mode() -> int:
    exit_code = execute_cli_command("docker version")
    if exit_code != 0:
        print("docker is not available.")
        return exit_code

    exit_code = execute_cli_command("docker compose version")
    if exit_code != 0:
        print("docker compose is not available.")
        return exit_code

    print("Starting Compose infra...")
    exit_code = execute_cli_command_in_dir("docker compose up -d", COMPOSE_DIR)
    if exit_code != 0:
        return exit_code

    for container_name in (
        COMPOSE_POSTGRES_CONTAINER,
        "k8s-cluster-kafka",
        COMPOSE_LOCALSTACK_CONTAINER,
    ):
        exit_code = wait_for_compose_container(container_name)
        if exit_code != 0:
            return exit_code

    exit_code = wait_for_compose_postgres()
    if exit_code != 0:
        return exit_code

    print("Compose infra ready on network k8s-cluster-local.")
    return 0


def install_infra(request: InstallInfraRequest) -> int:
    if request.mode == InstallMode.cluster:
        return install_cluster(request.namespace, request.with_kafka_ui)
    return install_compose_mode()
