import os
import sys

import yaml

from repo_paths import REPO_ROOT


def execute_cli_command(command: str) -> int:
    print(f'Executing command: {command}')
    return os.system(command)


def get_helm_releases(repository: str, namespace: str) -> list[str]:
    pipeline_path = os.path.join(REPO_ROOT, 'apps', repository, '.pipeline')
    with open(pipeline_path) as pipeline_file:
        pipeline = yaml.safe_load(pipeline_file)

    releases = []
    for step_args in pipeline.get('steps', {}).values():
        if step_args.get('kind') != 'install':
            continue
        if step_args.get('env') != namespace:
            continue
        if step_args.get('repo') != repository:
            continue
        releases.append(step_args['application'])

    return releases


def main(namespace: str, repository: str):
    releases = get_helm_releases(repository, namespace)
    if not releases:
        print(
            f'No install steps found for repository "{repository}" '
            f'in namespace "{namespace}".'
        )
        return

    exit_code = 0
    for release in releases:
        exit_code += execute_cli_command(
            f'helm uninstall {release} -n {namespace}'
        )

    if exit_code != 0:
        sys.exit(1)


if __name__ == '__main__':
    args = sys.argv[1:]

    if "-n" not in args:
        print("Namespace is required. Use -n flag to specify the namespace.")
        sys.exit(1)

    if "-r" not in args:
        print("Repository is required. Use -r flag to specify the repository.")
        sys.exit(1)

    namespace = args[args.index("-n") + 1]
    repository = args[args.index("-r") + 1]

    main(namespace, repository)
