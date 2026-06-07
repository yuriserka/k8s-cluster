import json
import os
import shlex
import shutil
import tempfile

import yaml
from dockerfile_parse import DockerfileParser

from k8s_cluster.commands.app.types import PublishAppRequest
from k8s_cluster.paths import REPO_ROOT, resolve_path
from k8s_cluster.utils.env_files import read_env_file


def run_docker_build(
    image: str,
    dockerfile_abs: str,
    build_context: str,
    use_minikube_docker: bool,
    build_args: dict | None = None,
) -> int:
    dockerfile_rel = os.path.relpath(dockerfile_abs, build_context)
    if dockerfile_rel.startswith(".."):
        dockerfile_for_build = dockerfile_abs
    else:
        dockerfile_for_build = dockerfile_rel
    build_arg_flags = "".join(
        f' --build-arg {shlex.quote(f"{key}={value}")}' for key, value in (build_args or {}).items()
    )
    inner = (
        f"cd {shlex.quote(build_context)} && "
        f"docker build -t {shlex.quote(image)} -f {shlex.quote(dockerfile_for_build)}{build_arg_flags} ."
    )
    if use_minikube_docker:
        inner = f'eval "$(minikube docker-env --shell bash)" && {inner}'
    cmd = f"bash -c {shlex.quote(inner)}"
    print(f"Executing command: {cmd}")
    return os.system(cmd)


def _insert_lines_before_instruction(dfp: DockerfileParser, instruction: str, lines: str) -> None:
    prefix = f"{instruction.upper()} "
    content_lines = dfp.content.splitlines(keepends=True)
    for index, line in enumerate(content_lines):
        if line.lstrip().upper().startswith(prefix):
            for insert_line in reversed(lines.splitlines(keepends=True)):
                content_lines.insert(index, insert_line)
            dfp.content = "".join(content_lines)
            return
    raise RuntimeError(f"Cannot find {instruction} instruction in Dockerfile")


def add_otel_to_java_dockerfile(
    dockerfile_path: str, java_agent_version: str, repository: str, enabled: bool, namespace: str, grafana_secrets: dict
) -> str:
    fd, updated_dockerfile_path = tempfile.mkstemp(
        suffix=".Dockerfile.instrumented",
        prefix="publish-",
    )
    os.close(fd)
    shutil.copy(dockerfile_path, updated_dockerfile_path)

    with open(updated_dockerfile_path, "r+") as dockerfile:
        dfp = DockerfileParser()
        dfp.content = dockerfile.read()

        cmd: list[str] = json.loads(dfp.cmd)
        java_arg = cmd.index("java")
        if "-jar" in cmd:
            jar_index = cmd.index("-jar")
            jvm_args = cmd[java_arg + 1 : jar_index]
            cmd_tail = cmd[jar_index:]
        else:
            jvm_args = []
            cmd_tail = cmd[java_arg + 1 :]

        otel_agent_url = (
            "https://github.com/open-telemetry/opentelemetry-java-instrumentation/"
            f"releases/download/v{java_agent_version}/opentelemetry-javaagent.jar"
        )
        otel_lines = (
            f"ADD {otel_agent_url} /app/opentelemetry-javaagent.jar\n"
            f'ENV OTEL_RESOURCE_ATTRIBUTES="service.name={repository},'
            f'service.namespace={namespace},deployment.environment={namespace}"\n'
            f'ENV OTEL_EXPORTER_OTLP_ENDPOINT={grafana_secrets.get("OTEL_EXPORTER_OTLP_ENDPOINT")}\n'
            f'ENV OTEL_EXPORTER_OTLP_PROTOCOL={grafana_secrets.get("OTEL_EXPORTER_OTLP_PROTOCOL")}\n'
            f'ENV OTEL_EXPORTER_OTLP_HEADERS={grafana_secrets.get("OTEL_EXPORTER_OTLP_HEADERS")}\n'
            f'ENV OTEL_JAVAAGENT_ENABLED="{json.dumps(enabled)}"\n'
        )
        _insert_lines_before_instruction(dfp, "CMD", otel_lines)

        dfp.cmd = json.dumps(
            [
                *cmd[: java_arg + 1],
                "-javaagent:/app/opentelemetry-javaagent.jar",
                *jvm_args,
                *cmd_tail,
            ]
        )

        with open(updated_dockerfile_path, "w") as updated_dockerfile:
            updated_dockerfile.write(dfp.content)

    return updated_dockerfile_path


def _inject_python_otel_pip_install(content: str, distro_version: str) -> str:
    otel_install = (
        "    && pip install --no-cache-dir \\\n"
        f"        opentelemetry-distro=={distro_version} \\\n"
        "        opentelemetry-exporter-otlp \\\n"
        "    && opentelemetry-bootstrap --action=install"
    )
    marker = "&& pip install --no-cache-dir -r requirements.txt"
    if marker not in content:
        raise RuntimeError("Cannot find requirements.txt pip install in Dockerfile deps stage")
    if "opentelemetry-distro" in content:
        return content
    return content.replace(marker, f"{marker} \\\n{otel_install}", 1)


def add_otel_to_python_dockerfile(
    dockerfile_path: str,
    distro_version: str,
    repository: str,
    enabled: bool,
    namespace: str,
    grafana_secrets: dict,
) -> str:
    fd, updated_dockerfile_path = tempfile.mkstemp(
        suffix=".Dockerfile.instrumented",
        prefix="publish-",
    )
    os.close(fd)
    shutil.copy(dockerfile_path, updated_dockerfile_path)

    with open(updated_dockerfile_path, "r+") as dockerfile:
        content = dockerfile.read()
        content = _inject_python_otel_pip_install(content, distro_version)

        if enabled:
            dfp = DockerfileParser()
            dfp.content = content
            otel_lines = (
                f'ENV OTEL_RESOURCE_ATTRIBUTES="service.name={repository},'
                f'service.namespace={namespace},deployment.environment={namespace}"\n'
                f'ENV OTEL_EXPORTER_OTLP_ENDPOINT={grafana_secrets.get("OTEL_EXPORTER_OTLP_ENDPOINT")}\n'
                f'ENV OTEL_EXPORTER_OTLP_PROTOCOL={grafana_secrets.get("OTEL_EXPORTER_OTLP_PROTOCOL")}\n'
                f'ENV OTEL_EXPORTER_OTLP_HEADERS={grafana_secrets.get("OTEL_EXPORTER_OTLP_HEADERS")}\n'
                f'ENV OTEL_TRACES_EXPORTER={grafana_secrets.get("OTEL_TRACES_EXPORTER", "otlp")}\n'
                f'ENV OTEL_METRICS_EXPORTER={grafana_secrets.get("OTEL_METRICS_EXPORTER", "otlp")}\n'
                f'ENV OTEL_LOGS_EXPORTER={grafana_secrets.get("OTEL_LOGS_EXPORTER", "otlp")}\n'
            )
            metric_interval = grafana_secrets.get("OTEL_METRIC_EXPORT_INTERVAL")
            metric_timeout = grafana_secrets.get("OTEL_METRIC_EXPORT_TIMEOUT")
            if metric_interval:
                otel_lines += f"ENV OTEL_METRIC_EXPORT_INTERVAL={metric_interval}\n"
            if metric_timeout:
                otel_lines += f"ENV OTEL_METRIC_EXPORT_TIMEOUT={metric_timeout}\n"
            _insert_lines_before_instruction(dfp, "ENTRYPOINT", otel_lines)
            content = dfp.content

        with open(updated_dockerfile_path, "w") as updated_dockerfile:
            updated_dockerfile.write(content)

    return updated_dockerfile_path


def handle_instrumentation(
    repository: str,
    namespace: str,
    dockerfile_path: str,
    build_context: str,
) -> str:
    resources_path = os.path.join(REPO_ROOT, "resources", repository, f"{namespace}.yaml")
    grafana_env_path = os.path.join(REPO_ROOT, "resources", "vault", "_admin", "grafana", namespace, ".env")

    with open(resources_path) as resources_file:
        resources = yaml.safe_load(resources_file)
    grafana_secrets = read_env_file(grafana_env_path)

    instrumentation = resources.get("instrumentation", {})
    is_enabled = instrumentation.get("enabled", False)
    dockerfile_abs = os.path.join(build_context, dockerfile_path)

    if "javaAgent" in instrumentation:
        java_agent = instrumentation.get("javaAgent", {})
        java_agent_version = java_agent.get("version", "latest")
        dockerfile_abs = add_otel_to_java_dockerfile(
            dockerfile_abs,
            java_agent_version,
            repository,
            is_enabled,
            namespace,
            grafana_secrets,
        )
        original_dockerfile = os.path.join(build_context, "Dockerfile")
        if os.path.isfile(original_dockerfile):
            os.system(f"rm -f {original_dockerfile}")
    elif "pythonAgent" in instrumentation:
        python_agent = instrumentation.get("pythonAgent", {})
        distro_version = python_agent.get("version", "latest")
        dockerfile_abs = add_otel_to_python_dockerfile(
            dockerfile_abs,
            distro_version,
            repository,
            is_enabled,
            namespace,
            grafana_secrets,
        )

    return dockerfile_abs


def publish_app(request: PublishAppRequest) -> int:
    tag = request.tag or "latest"
    image = f"{request.repository}-{request.namespace}:{tag}"
    build_context = resolve_path(request.app_path)
    original_dockerfile = os.path.join(build_context, request.dockerfile)
    instrumented_dockerfile = None
    try:
        dockerfile_abs = handle_instrumentation(
            request.repository, request.namespace, request.dockerfile, build_context
        )
        instrumented = dockerfile_abs != original_dockerfile
        if instrumented:
            instrumented_dockerfile = dockerfile_abs

        build_result = run_docker_build(
            image,
            dockerfile_abs,
            build_context,
            use_minikube_docker=request.use_minikube_docker,
            build_args=request.build_args,
        )
        if build_result != 0:
            target = "minikube docker" if request.use_minikube_docker else "local docker"
            print(f"Failed to build image {image} using {target}.")
        return build_result
    finally:
        if instrumented_dockerfile and os.path.isfile(instrumented_dockerfile):
            os.unlink(instrumented_dockerfile)
