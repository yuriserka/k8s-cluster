import json
from typing import Optional

import typer

from k8s_cluster.cli import exit_on_failure, make_cli_app
from k8s_cluster.commands.app.drop_service import drop_app
from k8s_cluster.commands.app.install_service import install_app
from k8s_cluster.commands.app.publish_service import publish_app
from k8s_cluster.commands.app.types import DropAppRequest, InstallAppRequest, PublishAppRequest

app = make_cli_app()


@app.command("drop")
def drop(
    repository: str = typer.Option(..., help="App folder under apps/"),
    namespace: str = typer.Option("dev", help="Kubernetes namespace (e.g. dev)"),
) -> None:
    exit_code = drop_app(DropAppRequest(repository=repository, namespace=namespace))
    exit_on_failure(exit_code, f"Failed to uninstall releases for {repository}")


@app.command("publish")
def publish(
    repository: str = typer.Option(..., help="Image/repository name (e.g. kafka-worker-api)"),
    dockerfile: str = typer.Option(..., help="Dockerfile path relative to --app-path"),
    app_path: str = typer.Option(..., help="Build context directory"),
    namespace: str = typer.Option(..., help="Namespace / environment (e.g. dev)"),
    tag: Optional[str] = typer.Option(None, help="Image tag (default: latest)"),
    use_minikube_docker: bool = typer.Option(
        False,
        help="Build against minikube Docker daemon (eval minikube docker-env)",
    ),
    build_args: Optional[str] = typer.Option(
        None, help='JSON object of Docker build-args (e.g. \'{"CONTAINER":"api"}\')'
    ),
) -> None:
    parsed_build_args = json.loads(build_args) if build_args else None
    exit_code = publish_app(
        PublishAppRequest(
            repository=repository,
            dockerfile=dockerfile,
            app_path=app_path,
            namespace=namespace,
            tag=tag,
            use_minikube_docker=use_minikube_docker,
            build_args=parsed_build_args,
        )
    )
    exit_on_failure(exit_code, f"Failed to publish app with repository: {repository}")


@app.command("install")
def install(
    application: str = typer.Option(..., help="Helm release / application name"),
    repository: str = typer.Option(..., help="App folder under apps/ (vault + chart output path)"),
    params_file: str = typer.Option(..., help="Kube params file under kube/<namespace>/ (e.g. api.yaml)"),
    app_path: str = typer.Option(..., help="App directory (chart context)"),
    namespace: str = typer.Option(..., help="Kubernetes namespace (e.g. dev)"),
    tag: Optional[str] = typer.Option(None, help="Image tag written into Helm values (default: latest)"),
    pipeline_id: Optional[str] = typer.Option(None, help="Pipeline run UUID (auto-generated if omitted)"),
    pipeline_started_at: Optional[str] = typer.Option(
        None, help="Pipeline start time ISO-8601 UTC (auto-generated if omitted)"
    ),
) -> None:
    exit_code = install_app(
        InstallAppRequest(
            application=application,
            repository=repository,
            params_file=params_file,
            app_path=app_path,
            namespace=namespace,
            tag=tag,
            pipeline_id=pipeline_id,
            pipeline_started_at=pipeline_started_at,
        )
    )
    exit_on_failure(exit_code, f"Installation of {application} failed")
