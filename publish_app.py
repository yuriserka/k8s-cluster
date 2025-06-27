import os
import yaml
import json
from dockerfile_parse import DockerfileParser


root_dir = os.getcwd()


def add_otel_to_java_dockerfile(dockerfile_path: str, java_agent_version: str, repository: str, enabled: bool) -> str:
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
            f'ENV OTEL_SERVICE_NAME="{repository}"\n'
            f'ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4318"\n'
            f'ENV OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"\n'
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


def handle_instrumentation(repository: str, namespace: str, dockerfile_path: str, path: str) -> str:
    os.chdir(root_dir)
    with open(f'./resources/{repository}/{namespace}.yaml') as resources_file:
        resources = yaml.safe_load(resources_file)

        instrumentation = resources.get('instrumentation', {})
        is_enabled = instrumentation.get('enabled', False)

        os.chdir(path)
        if 'javaAgent' in instrumentation:
            java_agent = instrumentation.get('javaAgent', {})
            java_agent_version = java_agent.get('version', 'latest')
            dockerfile_path = add_otel_to_java_dockerfile(
                dockerfile_path,
                java_agent_version,
                repository,
                is_enabled
            )
            os.system('rm -f Dockerfile')

    return dockerfile_path


def main(
    repository: str,
    dockerfile_path: str,
    namespace: str,
    intra_cluster: bool,
    path: str,
    tag: str = None
) -> int:
    tag = tag or 'latest'
    image = f'{repository}-{namespace}:{tag}'
    provider = 'minikube image' if intra_cluster else 'docker'
    new_dockerfile_path = handle_instrumentation(
        repository, namespace, dockerfile_path, path
    )

    build_result = os.system(
        f'{provider} build -t {image} -f {new_dockerfile_path} .'
    )
    if build_result == 0:
        if dockerfile_path != new_dockerfile_path:
            return os.system(f'rm -f {new_dockerfile_path}')
        return build_result

    print(f'Failed to build image {image} using {provider}.')
    if dockerfile_path != new_dockerfile_path:
        return os.system(f'rm -f {new_dockerfile_path}')

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

    os.chdir(path)

    exit_code = main(repository, dockerfile_path,
                     namespace, intra_cluster, path, tag)

    os.chdir(root_dir)

    if exit_code != 0:
        raise Exception(f'Failed to publish app with repository: {repository}')
