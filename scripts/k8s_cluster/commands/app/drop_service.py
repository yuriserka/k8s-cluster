import os

import yaml

from k8s_cluster.commands.app.types import DropAppRequest
from k8s_cluster.paths import REPO_ROOT
from k8s_cluster.services.helm import helm_uninstall


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


def drop_app(request: DropAppRequest) -> int:
    releases = get_helm_releases(request.repository, request.namespace)
    if not releases:
        print(f'No install steps found for repository "{request.repository}" in namespace "{request.namespace}".')
        return 0

    exit_code = 0
    for release in releases:
        exit_code += helm_uninstall(release, request.namespace)

    if exit_code == 0:
        print(f'App releases for "{request.repository}" removed from namespace "{request.namespace}".')
    return 0 if exit_code == 0 else 1
