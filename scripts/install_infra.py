import os
import shlex
import tempfile
import time
from enum import Enum

import typer
import yaml

from cli_common import exit_on_failure, make_cli_app
from infra_common import (
    READY_TIMEOUT_SECONDS,
    execute_cli_command,
    wait_for_kafka_ready,
    wait_for_localstack_ready,
    wait_for_postgresql_ready,
)
from repo_paths import REPO_ROOT

app = make_cli_app()

INFRA_DIR = os.path.join(REPO_ROOT, "apps", "infra")
COMPOSE_DIR = INFRA_DIR
COMPOSE_POSTGRES_CONTAINER = "k8s-cluster-postgres"
COMPOSE_LOCALSTACK_CONTAINER = "k8s-cluster-localstack"

HELM_REPOS = {
    "bitnami": "https://charts.bitnami.com/bitnami",
    "localstack": "https://localstack.github.io/helm-charts",
    "kafka-ui": "https://provectus.github.io/kafka-ui-charts",
}


class InstallMode(str, Enum):
    cluster = "cluster"
    compose = "compose"


def read_env_file(env_file: str) -> dict:
    if not os.path.isfile(env_file):
        raise FileNotFoundError(f"Environment file {env_file} does not exist.")

    secrets = {}
    with open(env_file) as secrets_file:
        for line in secrets_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            secrets[key.upper()] = value.strip()
    return secrets


def get_localstack_auth_token(namespace: str) -> str:
    env_file = os.path.join(REPO_ROOT, "resources", "vault", "_admin", "aws", namespace, ".env")
    secrets = read_env_file(env_file)
    token = secrets.get("LOCALSTACK_AUTH_TOKEN")
    if not token:
        raise ValueError(
            f"LOCALSTACK_AUTH_TOKEN is missing in {env_file}. " "Copy .env.example and set your LocalStack auth token."
        )
    return token


def ensure_helm_repos(repo_names: list[str]) -> int:
    for repo_name in repo_names:
        execute_cli_command(
            f"helm repo add {shlex.quote(repo_name)} {shlex.quote(HELM_REPOS[repo_name])} " "2>/dev/null || true"
        )
    return execute_cli_command("helm repo update")


def ensure_namespace(namespace: str) -> int:
    return execute_cli_command(
        f"minikube kubectl -- create namespace {shlex.quote(namespace)} "
        "--dry-run=client -o yaml | minikube kubectl -- apply -f -"
    )


def helm_upgrade_install(release: str, chart: str, namespace: str, values_file: str) -> int:
    return execute_cli_command(
        f"helm upgrade --install {shlex.quote(release)} {shlex.quote(chart)} "
        f"-n {shlex.quote(namespace)} -f {shlex.quote(values_file)}"
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
    return helm_upgrade_install("kafka-ui", "kafka-ui/kafka-ui", namespace, values_file)


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


def execute_cli_command_in_dir(command: str, cwd: str) -> int:
    print(f"Executing command in {cwd}: {command}")
    previous_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        return os.system(command)
    finally:
        os.chdir(previous_cwd)


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

    exit_code = ensure_helm_repos(repo_names)
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


@app.command()
def cli(
    mode: InstallMode = typer.Option(
        InstallMode.cluster,
        "--mode",
        help="cluster (minikube + Helm) or compose (Docker Compose from apps/infra)",
    ),
    namespace: str = typer.Option("dev", help="Kubernetes namespace (cluster mode only)"),
    with_kafka_ui: bool = typer.Option(
        False,
        "--with-kafka-ui",
        help="Install Kafka UI (cluster mode only; skipped by default)",
    ),
) -> None:
    try:
        if mode == InstallMode.cluster:
            exit_code = install_cluster(namespace, with_kafka_ui)
        else:
            if with_kafka_ui:
                typer.echo("--with-kafka-ui applies to cluster mode only.", err=True)
                raise typer.Exit(code=1)
            exit_code = install_compose_mode()
    except (FileNotFoundError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    exit_on_failure(exit_code, "")


if __name__ == "__main__":
    app()
