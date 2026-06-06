import os

import typer
import yaml

from cli_common import exit_on_failure, make_cli_app
from repo_paths import REPO_ROOT

app = make_cli_app()


def execute_cli_command(command: str) -> int:
    print(f"Executing command: {command}")
    return os.system(command)


def get_helm_releases(repository: str, namespace: str) -> list[str]:
    pipeline_path = os.path.join(REPO_ROOT, "apps", repository, ".pipeline")
    with open(pipeline_path) as pipeline_file:
        pipeline = yaml.safe_load(pipeline_file)

    releases = []
    for step_args in pipeline.get("steps", {}).values():
        if step_args.get("kind") != "install":
            continue
        if step_args.get("env") != namespace:
            continue
        if step_args.get("repo") != repository:
            continue
        releases.append(step_args["application"])

    return releases


def remove_all_pods(namespace: str, repository: str) -> int:
    releases = get_helm_releases(repository, namespace)
    if not releases:
        print(f'No install steps found for repository "{repository}" ' f'in namespace "{namespace}".')
        return 0

    exit_code = 0
    for release in releases:
        exit_code += execute_cli_command(f"helm uninstall {release} -n {namespace}")

    return 0 if exit_code == 0 else 1


@app.command()
def cli(
    namespace: str = typer.Option(..., help="Kubernetes namespace (e.g. dev)"),
    repository: str = typer.Option(..., help="App folder under apps/"),
) -> None:
    exit_code = remove_all_pods(namespace, repository)
    exit_on_failure(exit_code, f"Failed to uninstall releases for {repository}")


if __name__ == "__main__":
    app()
