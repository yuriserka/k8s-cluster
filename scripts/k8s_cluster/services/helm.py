import shlex

from k8s_cluster.utils.shell import execute_cli_command


def helm_upgrade_install(release: str, chart: str, namespace: str, values_file: str) -> int:
    return execute_cli_command(
        f"helm upgrade --install {shlex.quote(release)} {shlex.quote(chart)} "
        f"-n {shlex.quote(namespace)} -f {shlex.quote(values_file)}"
    )


def helm_uninstall(release: str, namespace: str) -> int:
    print(f'Uninstalling Helm release "{release}" from namespace "{namespace}"...')
    return execute_cli_command(f"helm uninstall {shlex.quote(release)} -n {shlex.quote(namespace)} --ignore-not-found")


def ensure_helm_repos(repo_names: list[str], helm_repos: dict[str, str]) -> int:
    for repo_name in repo_names:
        execute_cli_command(
            f"helm repo add {shlex.quote(repo_name)} {shlex.quote(helm_repos[repo_name])} " "2>/dev/null || true"
        )
    return execute_cli_command("helm repo update")
