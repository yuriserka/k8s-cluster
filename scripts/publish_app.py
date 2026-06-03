import os
import shlex
import yaml
import json
from dockerfile_parse import DockerfileParser

from repo_paths import REPO_ROOT, resolve_path


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
    build_arg_flags = ''.join(
        f' --build-arg {shlex.quote(f"{key}={value}")}'
        for key, value in (build_args or {}).items()
    )
    inner = (
        f'cd {shlex.quote(build_context)} && '
        f'docker build -t {shlex.quote(image)} -f {shlex.quote(dockerfile_rel)}{build_arg_flags} .'
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
            key, value = line.split('=', maxsplit=1)
            all_secrets[f"{key.upper()}"] = value.strip()

    return all_secrets


def add_otel_to_java_dockerfile(
    dockerfile_path: str,
    java_agent_version: str,
    repository: str,
    enabled: bool,
    namespace: str,
    grafana_secrets: dict
) -> str:
    updated_dockerfile_path = dockerfile_path.replace(
        'Dockerfile',
        'Dockerfile.instrumented'
    )

    os.system(f'cp {dockerfile_path} {updated_dockerfile_path}')
    with open(updated_dockerfile_path, 'r') as dockerfile:
        dfp = DockerfileParser()
        dfp.content = dockerfile.read()

        cmd: list[str] = json.loads(dfp.cmd)
        jar_args = cmd.index('-jar')
        java_arg = cmd.index('java')

        dfp.add_lines_at(
            f'CMD {dfp.cmd}\n',
            f'ADD https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v{java_agent_version}/opentelemetry-javaagent.jar /app/opentelemetry-javaagent.jar\n'
            f'ENV OTEL_RESOURCE_ATTRIBUTES="service.name={repository},service.namespace={namespace},deployment.environment={namespace}"\n'
            f'ENV OTEL_EXPORTER_OTLP_ENDPOINT={grafana_secrets.get("OTEL_EXPORTER_OTLP_ENDPOINT")}\n'
            f'ENV OTEL_EXPORTER_OTLP_PROTOCOL={grafana_secrets.get("OTEL_EXPORTER_OTLP_PROTOCOL")}\n'
            f'ENV OTEL_EXPORTER_OTLP_HEADERS={grafana_secrets.get("OTEL_EXPORTER_OTLP_HEADERS")}\n'
            f'ENV OTEL_JAVAAGENT_ENABLED="{json.dumps(enabled)}"\n',
            after=False,
        )

        dfp.cmd = json.dumps([
            *cmd[:java_arg + 1],
            '-javaagent:/app/opentelemetry-javaagent.jar',
            *cmd[jar_args:]
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
    dockerfile_abs = handle_instrumentation(
        repository, namespace, dockerfile_path, build_context
    )
    instrumented = dockerfile_abs != original_dockerfile

    build_result = run_docker_build(
        image,
        dockerfile_abs,
        build_context,
        use_minikube_docker=intra_cluster,
        build_args=build_args,
    )
    if build_result == 0:
        if instrumented:
            os.system(f'rm -f {dockerfile_abs}')
        return build_result

    target = 'minikube docker' if intra_cluster else 'local docker'
    print(f'Failed to build image {image} using {target}.')
    if instrumented:
        os.system(f'rm -f {dockerfile_abs}')

    return build_result


if __name__ == '__main__':
    args = os.sys.argv[1:]

    if "-n" not in args:
        print("Namespace is required to publish the app. Use -n flag to specify the namespace.")
        exit(1)

    if "-d" not in args:
        print("Dockerfile path is required to publish the app. Use -d flag to specify the dockerfile path.")
        exit(1)

    if "-r" not in args:
        print("Repository is required to publish the app. Use -r flag to specify the repository.")
        exit(1)

    if "-p" not in args:
        print("Path is required to publish the app. Use -p flag to specify the path.")
        exit(1)

    namespace = args[args.index("-n") + 1]
    dockerfile_path = args[args.index("-d") + 1]
    repository = args[args.index("-r") + 1]
    path = args[args.index("-p") + 1]
    tag = args[args.index("-t") + 1] if "-t" in args else None
    intra_cluster = "-k" in args
    build_args = json.loads(args[args.index("-b") + 1]) if "-b" in args else None

    exit_code = main(
        repository, dockerfile_path, namespace, intra_cluster, path, tag, build_args
    )

    if exit_code != 0:
        raise Exception(f'Failed to publish app with repository: {repository}')
