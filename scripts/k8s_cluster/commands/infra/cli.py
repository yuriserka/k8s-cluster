from typing import Optional

import typer

from k8s_cluster.cli import exit_on_failure, make_cli_app
from k8s_cluster.commands.infra.drop_service import drop_infra
from k8s_cluster.commands.infra.install_service import install_infra
from k8s_cluster.commands.infra.types import (
    DropInfraRequest,
    DropMode,
    InfraService,
    InstallInfraRequest,
    InstallMode,
)

app = make_cli_app()


@app.command("install")
def install(
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
        if mode == InstallMode.compose and with_kafka_ui:
            typer.echo("--with-kafka-ui applies to cluster mode only.", err=True)
            raise typer.Exit(code=1)
        exit_code = install_infra(InstallInfraRequest(mode=mode, namespace=namespace, with_kafka_ui=with_kafka_ui))
    except (FileNotFoundError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    exit_on_failure(exit_code, "")


@app.command("drop")
def drop(
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
    if mode == DropMode.cluster and volumes:
        typer.echo("--volumes applies to compose mode only.", err=True)
        raise typer.Exit(code=1)

    exit_code = drop_infra(
        DropInfraRequest(
            mode=mode,
            namespace=namespace,
            services=service,
            remove_volumes=volumes,
        )
    )
    exit_on_failure(exit_code, "")
