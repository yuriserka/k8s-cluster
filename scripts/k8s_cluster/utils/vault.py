import os

from k8s_cluster.paths import REPO_ROOT
from k8s_cluster.services.pod_wait import DEFAULT_POSTGRES_SERVICE

DEFAULT_POSTGRES_PORT = "5432"

INFRA_ONLY_KEYS_BY_RESOURCE = {
    "aws": {"AWS_LOCALSTACK_AUTH_TOKEN"},
}


def load_vault_env(
    vault_target: str,
    namespace: str,
    include_resources: set[str] | None = None,
) -> dict:
    vault_root = os.path.join(REPO_ROOT, "resources", "vault", vault_target)
    if not os.path.isdir(vault_root):
        return {}

    all_secrets = {}
    for resource in sorted(os.listdir(vault_root)):
        if include_resources is not None and resource not in include_resources:
            continue

        env_dir = os.path.join(vault_root, resource, namespace)
        env_file = os.path.join(env_dir, ".env")
        if not os.path.isfile(env_file):
            continue

        with open(env_file) as secrets_file:
            for line in secrets_file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                all_secrets[f"{resource.upper()}_{key.upper()}"] = value.strip().strip('"')

    return all_secrets


def exclude_infra_only_keys(secrets: dict, resource: str) -> dict:
    blocked = INFRA_ONLY_KEYS_BY_RESOURCE.get(resource, set())
    return {key: value for key, value in secrets.items() if key not in blocked}


def resolve_database_host(secrets: dict, default: str = DEFAULT_POSTGRES_SERVICE) -> str:
    return secrets.get("DATABASE_CLUSTER_HOST", default)


def normalize_database_secret_env(secrets: dict) -> dict:
    database_env = {key: value for key, value in secrets.items() if key.startswith("DATABASE_")}
    if not database_env:
        return {}

    cluster_host = resolve_database_host(database_env)
    database_env["DATABASE_HOST"] = cluster_host
    database_env.pop("DATABASE_CLUSTER_HOST", None)
    database_env.setdefault("DATABASE_PORT", DEFAULT_POSTGRES_PORT)

    return database_env


def get_secrets_for_app(
    repository: str,
    namespace: str,
    shared_resources: list[str] | None = None,
) -> dict:
    secrets = load_vault_env(repository, namespace)
    secrets = normalize_database_secret_env(secrets)

    for resource in shared_resources or []:
        admin_keys = load_vault_env("_admin", namespace, include_resources={resource})
        admin_keys = exclude_infra_only_keys(admin_keys, resource)
        secrets = {**secrets, **admin_keys}

    return secrets
