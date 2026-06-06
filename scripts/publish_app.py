import json
import os
import shlex
import shutil
import tempfile
from typing import Optional

import typer
import yaml
from dockerfile_parse import DockerfileParser

from cli_common import exit_on_failure, make_cli_app
from repo_paths import REPO_ROOT, resolve_path

app = make_cli_app()


def run_docker_build(
    image: str,
    dockerfile_abs: str,
    build_context: str,
    use_minikube_docker: bool,
    build_args: dict | None = None,
) -> int:
    """Build from build_context using a relative Dockerfile path.

    Avoids passing WSL absolute paths to minikube image build / Docker Desktop,
    which often fails with: lstat /home/<user>: no such file or directory
    """
    dockerfile_rel = os.path.relpath(dockerfile_abs, build_context)
    if dockerfile_rel.startswith('..'):
        dockerfile_for_build = dockerfile_abs
    else:
        dockerfile_for_build = dockerfile_rel
    build_arg_flags = ''.join(
        f' --build-arg {shlex.quote(f"{key}={value}")}'
        for key, value in (build_args or {}).items()
    )
    inner = (
        f'cd {shlex.quote(build_context)} && '
        f'docker build -t {shlex.quote(image)} -f {shlex.quote(dockerfile_for_build)}{build_arg_flags} .'
    )
    if use_minikube_docker:
        inner = f'eval "$(minikube docker-env --shell bash)" && {inner}'
    # os.system uses /bin/sh (dash); default minikube docker-env is fish ("set -gx").
    cmd = f'bash -c {shlex.quote(inner)}'
    print(f'Executing command: {cmd}')
    return os.system(cmd)


def read_env_file(env_file: str):
    if not os.path.isfile(env_file):
        raise FileNotFoundError(f'Environment file {env_file} does not exist.')

    all_secrets = {}
    with open(env_file) as secrets_file:
        lines = secrets_file.readlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            line = line.split('#', 1)[0]
            key, value = line.split('=', maxsplit=1)
            all_secrets[f"{key.upper()}"] = value.strip()

    return all_secrets


def _insert_lines_before_instruction(
    dfp: DockerfileParser, instruction: str, lines: str
) -> None:
    """Insert lines before the first Dockerfile instruction (handles multi-line CMD)."""
    prefix = f'{instruction.upper()} '
    content_lines = dfp.content.splitlines(keepends=True)
    for index, line in enumerate(content_lines):
        if line.lstrip().upper().startswith(prefix):
            for insert_line in reversed(lines.splitlines(keepends=True)):
                content_lines.insert(index, insert_line)
            dfp.content = ''.join(content_lines)
            return
    raise RuntimeError(f'Cannot find {instruction} instruction in Dockerfile')


def add_otel_to_java_dockerfile(
    dockerfile_path: str,
    java_agent_version: str,
    repository: str,
    enabled: bool,
    namespace: str,
    grafana_secrets: dict
) -> str:
    fd, updated_dockerfile_path = tempfile.mkstemp(
        suffix='.Dockerfile.instrumented',
        prefix='publish-',
    )
    os.close(fd)
    shutil.copy(dockerfile_path, updated_dockerfile_path)

    with open(updated_dockerfile_path, 'r+') as dockerfile:
        dfp = DockerfileParser()
        dfp.content = dockerfile.read()

        cmd: list[str] = json.loads(dfp.cmd)
        java_arg = cmd.index('java')
        if '-jar' in cmd:
            jar_index = cmd.index('-jar')
            jvm_args = cmd[java_arg + 1:jar_index]
            cmd_tail = cmd[jar_index:]
        else:
            jvm_args = []
            cmd_tail = cmd[java_arg + 1:]

        otel_lines = (
            f'ADD https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v{java_agent_version}/opentelemetry-javaagent.jar /app/opentelemetry-javaagent.jar\n'
            f'ENV OTEL_RESOURCE_ATTRIBUTES="service.name={repository},service.namespace={namespace},deployment.environment={namespace}"\n'
            f'ENV OTEL_EXPORTER_OTLP_ENDPOINT={grafana_secrets.get("OTEL_EXPORTER_OTLP_ENDPOINT")}\n'
            f'ENV OTEL_EXPORTER_OTLP_PROTOCOL={grafana_secrets.get("OTEL_EXPORTER_OTLP_PROTOCOL")}\n'
            f'ENV OTEL_EXPORTER_OTLP_HEADERS={grafana_secrets.get("OTEL_EXPORTER_OTLP_HEADERS")}\n'
            f'ENV OTEL_JAVAAGENT_ENABLED="{json.dumps(enabled)}"\n'
        )
        _insert_lines_before_instruction(dfp, 'CMD', otel_lines)

        dfp.cmd = json.dumps([
            *cmd[:java_arg + 1],
            '-javaagent:/app/opentelemetry-javaagent.jar',
            *jvm_args,
            *cmd_tail,
        ])

        with open(updated_dockerfile_path, 'w') as updated_dockerfile:
            updated_dockerfile.write(dfp.content)

    return updated_dockerfile_path


def handle_instrumentation(
    repository: str,
    namespace: str,
    dockerfile_path: str,
    build_context: str,
) -> str:
    resources_path = os.path.join(
        REPO_ROOT, 'resources', repository, f'{namespace}.yaml'
    )
    grafana_env_path = os.path.join(
        REPO_ROOT, 'resources', 'vault', '_admin', 'grafana', namespace, '.env'
    )

    with open(resources_path) as resources_file:
        resources = yaml.safe_load(resources_file)
    grafana_secrets = read_env_file(grafana_env_path)

    instrumentation = resources.get('instrumentation', {})
    is_enabled = instrumentation.get('enabled', False)
    dockerfile_abs = os.path.join(build_context, dockerfile_path)

    if 'javaAgent' in instrumentation:
        java_agent = instrumentation.get('javaAgent', {})
        java_agent_version = java_agent.get('version', 'latest')
        dockerfile_abs = add_otel_to_java_dockerfile(
            dockerfile_abs,
            java_agent_version,
            repository,
            is_enabled,
            namespace,
            grafana_secrets,
        )
        original_dockerfile = os.path.join(build_context, 'Dockerfile')
        if os.path.isfile(original_dockerfile):
            os.system(f'rm -f {original_dockerfile}')

    return dockerfile_abs


def main(
    repository: str,
    dockerfile_path: str,
    namespace: str,
    intra_cluster: bool,
    path: str,
    tag: str = None,
    build_args: dict | None = None,
) -> int:
    tag = tag or 'latest'
    image = f'{repository}-{namespace}:{tag}'
    build_context = resolve_path(path)
    original_dockerfile = os.path.join(build_context, dockerfile_path)
    instrumented_dockerfile = None
    try:
        dockerfile_abs = handle_instrumentation(
            repository, namespace, dockerfile_path, build_context
        )
        instrumented = dockerfile_abs != original_dockerfile
        if instrumented:
            instrumented_dockerfile = dockerfile_abs

        build_result = run_docker_build(
            image,
            dockerfile_abs,
            build_context,
            use_minikube_docker=intra_cluster,
            build_args=build_args,
        )
        if build_result != 0:
            target = 'minikube docker' if intra_cluster else 'local docker'
            print(f'Failed to build image {image} using {target}.')
        return build_result
    finally:
        if instrumented_dockerfile and os.path.isfile(instrumented_dockerfile):
            os.unlink(instrumented_dockerfile)


@app.command()
def cli(
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
        None, help="JSON object of Docker build-args (e.g. '{\"CONTAINER\":\"api\"}')"
    ),
) -> None:
    parsed_build_args = json.loads(build_args) if build_args else None
    exit_code = main(
        repository,
        dockerfile,
        namespace,
        use_minikube_docker,
        app_path,
        tag,
        parsed_build_args,
    )
    exit_on_failure(exit_code, f"Failed to publish app with repository: {repository}")


if __name__ == '__main__':
    app()
