import os

from k8s_cluster.paths import REPO_ROOT
from k8s_cluster.utils.shell import execute_cli_command


def handle_clone_step(repository: str, temp_folder_path: str) -> int:
    app_source = os.path.join(REPO_ROOT, "apps", repository)
    gitignore = os.path.join(app_source, ".gitignore")
    os.makedirs(temp_folder_path, exist_ok=True)
    return execute_cli_command(f"rsync -r {app_source}/ {temp_folder_path}/ --exclude-from={gitignore}")
