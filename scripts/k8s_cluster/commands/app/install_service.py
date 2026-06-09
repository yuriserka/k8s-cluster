import os
import tempfile
import uuid
from datetime import datetime, timezone

import yaml

from k8s_cluster.commands.app.types import InstallAppRequest
from k8s_cluster.paths import REPO_ROOT, resolve_path
from k8s_cluster.utils.vault import get_secrets_for_app

KUBE_ONLY_KEYS = {
    "cmd",
    "args",
    "port",
    "vaultShared",
    "livenessProbePath",
    "readinessProbePath",
    "livenessProbeCmd",
    "readinessProbeCmd",
    "nameOverride",
    "fullnameOverride",
    "podLabels",
    "service",
}

ALLOWED_COMPONENTS = frozenset({"api", "worker"})

DEFAULT_PROBE_TIMING = {
    "initialDelaySeconds": 15,
    "periodSeconds": 5,
    "timeoutSeconds": 60,
}

DEFAULT_STARTUP_PROBE_TIMING = {
    "failureThreshold": 30,
    "periodSeconds": 10,
}

PROBE_HTTP_HEADERS = [{"name": "Host", "value": "localhost"}]


def get_values_template_for(namespace: str) -> dict:
    values_path = os.path.join(REPO_ROOT, "envs", namespace, "values.yaml")
    with open(values_path) as values_file:
        return yaml.safe_load(values_file)


def get_declared_values_for_app(env_file: str, namespace: str, path: str) -> dict:
    override_path = os.path.join(resolve_path(path), "kube", namespace, env_file)
    with open(override_path) as override_file:
        return yaml.safe_load(override_file) or {}


def get_resources_for(app_name: str, namespace: str) -> dict:
    resources_path = os.path.join(REPO_ROOT, "resources", app_name, f"{namespace}.yaml")
    with open(resources_path) as resources_file:
        return yaml.safe_load(resources_file)


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


def _probe_section(values: dict, key: str) -> dict:
    probe = values.get(key)
    return probe if isinstance(probe, dict) else {}


def handle_probes(values: dict, key: str | None = None, value=None):
    if key is None and value is None:
        liveness_probe = _probe_section(values, "livenessProbe")
        readiness_probe = _probe_section(values, "readinessProbe")
        startup_probe = _probe_section(values, "startupProbe")

        has_liveness_http = liveness_probe.get("httpGet") is not None
        has_readiness_http = readiness_probe.get("httpGet") is not None
        has_liveness_exec = liveness_probe.get("exec") is not None
        has_readiness_exec = readiness_probe.get("exec") is not None
        has_startup_http = startup_probe.get("httpGet") is not None
        has_startup_exec = startup_probe.get("exec") is not None

        if not has_liveness_http and not has_liveness_exec:
            update_value(values, "livenessProbe", None)
        if not has_readiness_http and not has_readiness_exec:
            update_value(values, "readinessProbe", None)
        if not has_startup_http and not has_startup_exec:
            update_value(values, "startupProbe", None)

        return

    real_key = "livenessProbe" if "liveness" in key else "readinessProbe"
    probe = None
    if "Cmd" in key:
        probe = {**_probe_section(values, real_key), "exec": {"command": value}, **DEFAULT_PROBE_TIMING}
        update_value(values, real_key, probe)
    elif "Path" in key:
        probe = {
            **_probe_section(values, real_key),
            "httpGet": {
                "path": value,
                "port": "http",
                "httpHeaders": PROBE_HTTP_HEADERS,
            },
            **DEFAULT_PROBE_TIMING,
        }
        update_value(values, real_key, probe)

    if probe is not None and real_key == "livenessProbe":
        update_value(values, "startupProbe", {**probe, **DEFAULT_STARTUP_PROBE_TIMING})


def resolve_pipeline_metadata(
    pipeline_id: str | None,
    pipeline_started_at: str | None,
) -> tuple[str, str]:
    return (
        pipeline_id or str(uuid.uuid4()),
        pipeline_started_at or datetime.now(timezone.utc).isoformat(),
    )


def resolve_helm_names(application: str, namespace: str) -> tuple[str, str]:
    return application, f"{application}-{namespace}"


def resolve_allowed_hosts(fullname: str) -> str:
    service_host = f"{fullname}-service"
    return f"localhost,127.0.0.1,{service_host},.svc.cluster.local"


def apply_api_allowed_hosts(values_ref: dict, component: str, fullname: str) -> None:
    if component != "api":
        return
    env = values_ref.setdefault("env", {})
    if "ALLOWED_HOSTS" in env:
        return
    env["ALLOWED_HOSTS"] = resolve_allowed_hosts(fullname)


def resolve_component_label(resources: dict) -> dict:
    component = resources.get("component")
    if component not in ALLOWED_COMPONENTS:
        raise ValueError(f"component must be one of {sorted(ALLOWED_COMPONENTS)}, got {component!r}")
    return {"app.kubernetes.io/component": component}


def helm_resources_from_app_resources(resources: dict) -> dict:
    return {key: value for key, value in resources.items() if key != "component"}


def resolve_service_enabled(component: str, override_value: dict) -> bool:
    has_port = "port" in override_value
    if component == "api":
        if not has_port:
            raise ValueError("component 'api' requires port in kube params")
        return True
    if component == "worker":
        return has_port
    raise ValueError(f"component must be one of {sorted(ALLOWED_COMPONENTS)}, got {component!r}")


def apply_service_enabled(values_ref: dict, component: str, override_value: dict) -> None:
    service = values_ref.setdefault("service", {})
    service["enabled"] = resolve_service_enabled(component, override_value)


def merge_values_dict(values_ref: dict, overrides: dict) -> None:
    for key, value in overrides.items():
        if key not in values_ref:
            values_ref[key] = value
        elif isinstance(values_ref[key], dict) and isinstance(value, dict):
            values_ref[key] = {**values_ref[key], **value}
        else:
            values_ref[key] = value


def apply_kube_override(values_ref: dict, key: str, value) -> None:
    if "Probe" in key:
        handle_probes(values_ref, key, value)
    if key in mapping_kube_to_helm_values:
        update_value(values_ref, mapping_kube_to_helm_values[key], value)


def apply_override_values(values_ref: dict, override_value: dict) -> None:
    for key, value in override_value.items():
        if key in KUBE_ONLY_KEYS or key == "env":
            apply_kube_override(values_ref, key, value)
            continue

        apply_kube_override(values_ref, key, value)
        if key in mapping_kube_to_helm_values or "Probe" in key:
            continue

        if key not in values_ref:
            values_ref[key] = value
        elif isinstance(values_ref[key], dict) and isinstance(value, dict):
            values_ref[key] = {**values_ref[key], **value}
        else:
            values_ref[key] = value


def build_install_values(request: InstallAppRequest, tag: str) -> dict:
    values = get_values_template_for(request.namespace)
    override_value = get_declared_values_for_app(request.params_file, request.namespace, request.app_path)
    app_resources = get_resources_for(request.application, request.namespace)

    vault_shared = override_value.get("vaultShared", [])
    values_ref = dict(values)
    name_override, fullname_override = resolve_helm_names(request.application, request.namespace)
    values_ref["nameOverride"] = name_override
    values_ref["fullnameOverride"] = fullname_override
    values_ref["podLabels"] = resolve_component_label(app_resources)
    update_value(values_ref, "image.repository", f"{request.application}-{request.namespace}")
    update_value(values_ref, "image.tag", tag)
    values_ref["env"] = override_value.get("env", {})
    values_ref["secretEnv"] = get_secrets_for_app(request.repository, request.namespace, vault_shared)

    apply_override_values(values_ref, override_value)
    apply_api_allowed_hosts(values_ref, app_resources["component"], fullname_override)
    handle_probes(values_ref)
    apply_service_enabled(values_ref, app_resources["component"], override_value)
    merge_values_dict(values_ref, helm_resources_from_app_resources(app_resources))

    resolved_pipeline_id, resolved_pipeline_started_at = resolve_pipeline_metadata(
        request.pipeline_id,
        request.pipeline_started_at,
    )
    values_ref["podAnnotations"] = {
        **values_ref.get("podAnnotations", {}),
        "pipeline_id": resolved_pipeline_id,
        "pipeline_deployed_at": resolved_pipeline_started_at,
    }
    return values_ref, resolved_pipeline_id


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


def install_app(request: InstallAppRequest) -> int:
    tag = request.tag or "latest"
    values_ref, _ = build_install_values(request, tag)
    return execute_helm_commands(request.application, request.repository, request.namespace, values_ref)
