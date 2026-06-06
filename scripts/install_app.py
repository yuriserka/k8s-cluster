import os
import tempfile
import uuid
import yaml
from datetime import datetime, timezone
from typing import Optional

import typer

from cli_common import exit_on_failure, make_cli_app
from repo_paths import REPO_ROOT, resolve_path

app = make_cli_app()


def get_values_template_for(namespace: str) -> dict:
    values_path = os.path.join(REPO_ROOT, "envs", namespace, "values.yaml")
    with open(values_path) as values_file:
        return yaml.safe_load(values_file)


def get_declared_values_for_app(env_file: str, namespace: str, path: str) -> dict:
    override_path = os.path.join(resolve_path(path), "kube", namespace, env_file)
    with open(override_path) as override_file:
        return yaml.safe_load(override_file)


def get_secrets_for_app(repository: str, namespace: str) -> dict:
    all_secrets = {}
    vault_root = os.path.join(REPO_ROOT, "resources", "vault", repository)
    resource_directories = os.listdir(vault_root)
    for resource in resource_directories:
        env_dir = os.path.join(vault_root, resource, namespace)
        if not os.path.isdir(env_dir):
            continue

        with open(os.path.join(env_dir, ".env")) as secrets_file:
            lines = secrets_file.readlines()
            for line in lines:
                key, value = line.split("=")
                all_secrets[f"{resource.upper()}_{key.upper()}"] = value.strip()

    return all_secrets


def get_resources_for(app_name: str, namespace: str) -> dict:
    resources_path = os.path.join(REPO_ROOT, "resources", app_name, f"{namespace}.yaml")
    with open(resources_path) as resources_file:
        return yaml.safe_load(resources_file)


def execute_helm_commands(app_name: str, repository: str, namespace: str, values: dict) -> int:
    chart_path = os.path.join(REPO_ROOT, "envs", namespace)
    rendered_manifest = os.path.join(REPO_ROOT, "apps", repository, f"{app_name}-{namespace}.yaml")

    os.makedirs(os.path.dirname(rendered_manifest), exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        prefix=f"{app_name}-values-",
        delete=False,
    ) as result:
        yaml.safe_dump(
            values,
            result,
            sort_keys=False,
            default_flow_style=None,
            allow_unicode=True,
        )
        values_file = result.name

    try:
        template_exit = os.system(
            f"helm template {app_name} {chart_path} -n {namespace} -f {values_file} >" f" {rendered_manifest}"
        )
        if template_exit != 0:
            return template_exit

        return os.system(f"helm upgrade --install {app_name} {chart_path} -n {namespace} -f {values_file}")
    finally:
        os.unlink(values_file)


def update_value(obj: dict, path: str, value):
    def update_deep_nested_dict(nested_dict, keys, new_value):
        if len(keys) == 1:
            nested_dict[keys[0]] = new_value
        else:
            update_deep_nested_dict(nested_dict[keys[0]], keys[1:], new_value)

    keys = path.split(".")
    return update_deep_nested_dict(obj, keys, value)


mapping_kube_to_helm_values = {
    "cmd": "container.cmd",
    "args": "container.args",
    "port": "service.port",
}


def handle_probes(values: dict, key: str | None = None, value=None):
    if key is None and value is None:
        has_liveness_http = values.get("livenessProbe").get("httpGet") is not None
        has_readines_http = values.get("readinessProbe").get("httpGet") is not None
        has_liveness_exec = values.get("livenessProbe").get("exec") is not None
        has_readiness_exec = values.get("readinessProbe").get("exec") is not None
        has_startup_http = values.get("startupProbe").get("httpGet") is not None
        has_startup_exec = values.get("startupProbe").get("exec") is not None

        if not has_liveness_http and not has_liveness_exec:
            update_value(values, "livenessProbe", None)
        if not has_readines_http and not has_readiness_exec:
            update_value(values, "readinessProbe", None)
        if not has_startup_http and not has_startup_exec:
            update_value(values, "startupProbe", None)

        return

    real_key = "livenessProbe" if "liveness" in key else "readinessProbe"
    probe = None
    if "Cmd" in key:
        probe = {**values.get(real_key, {}), "exec": {"command": value}}
        update_value(values, real_key, probe)
    elif "Path" in key:
        probe = {**values.get(real_key, {}), "httpGet": {"path": value, "port": "http"}}
        update_value(values, real_key, probe)

    if probe is not None and real_key == "livenessProbe":
        update_value(values, "startupProbe", probe)


def resolve_pipeline_metadata(
    pipeline_id: str | None,
    pipeline_started_at: str | None,
) -> tuple[str, str]:
    return (
        pipeline_id or str(uuid.uuid4()),
        pipeline_started_at or datetime.now(timezone.utc).isoformat(),
    )


def install_app(
    application: str,
    repository: str,
    environment_file: str,
    namespace: str,
    path: str,
    tag: str = None,
    pipeline_id: str | None = None,
    pipeline_started_at: str | None = None,
) -> int:
    # os.system(f'k create namespace {namespace}')
    values = get_values_template_for(namespace)
    override_value = get_declared_values_for_app(environment_file, namespace, path)

    # declared values in app/kube is prioritized over values in envs
    override_value = {
        **override_value,
        "env": {
            **get_secrets_for_app(repository, namespace),
            **override_value.get("env", {}),
        },
    }

    values_ref = dict(values)
    update_value(values_ref, "image.repository", f"{application}-{namespace}")
    update_value(values_ref, "image.tag", tag)
    for key, value in override_value.items():
        if "Probe" in key:
            handle_probes(values_ref, key, value)
        if key in mapping_kube_to_helm_values:
            update_value(values_ref, mapping_kube_to_helm_values.get(key), value)
        elif key not in values_ref:
            values_ref[key] = value
        else:
            values_ref[key] = {**values_ref[key], **value}

    handle_probes(values_ref)
    resources = get_resources_for(application, namespace)
    for key, value in resources.items():
        if key not in values_ref:
            values_ref[key] = value
        else:
            values_ref[key] = {**values_ref[key], **value}

    resolved_pipeline_id, resolved_pipeline_started_at = resolve_pipeline_metadata(
        pipeline_id,
        pipeline_started_at,
    )
    values_ref["podAnnotations"] = {
        **values_ref.get("podAnnotations", {}),
        "pipeline_id": resolved_pipeline_id,
        "pipeline_deployed_at": resolved_pipeline_started_at,
    }

    return execute_helm_commands(application, repository, namespace, values_ref)


def main(
    application: str,
    repository: str,
    environment_file: str,
    namespace: str,
    path: str,
    tag: str,
    pipeline_id: str | None = None,
    pipeline_started_at: str | None = None,
) -> int:
    tag = tag or "latest"
    return install_app(
        application,
        repository,
        environment_file,
        namespace,
        path,
        tag,
        pipeline_id,
        pipeline_started_at,
    )


@app.command()
def cli(
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
    exit_code = main(
        application,
        repository,
        params_file,
        namespace,
        app_path,
        tag,
        pipeline_id,
        pipeline_started_at,
    )
    exit_on_failure(exit_code, f"Installation of {application} failed")


if __name__ == "__main__":
    app()
