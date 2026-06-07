import os
import shlex

from k8s_cluster.commands.database.types import CreateDatabaseRequest
from k8s_cluster.paths import REPO_ROOT
from k8s_cluster.utils.env_files import read_env_file
from k8s_cluster.utils.shell import execute_cli_command


def quote_pg_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def get_database_admin_credentials(namespace: str) -> dict:
    env_dir = os.path.join(REPO_ROOT, "resources", "vault", "_admin", "database", namespace)
    if not os.path.isdir(env_dir):
        raise FileNotFoundError(f"Environment directory {env_dir} does not exist.")
    return read_env_file(os.path.join(env_dir, ".env"))


def get_database_credentials(repository: str, namespace: str) -> dict:
    env_dir = os.path.join(REPO_ROOT, "resources", "vault", repository, "database", namespace)
    if not os.path.isdir(env_dir):
        raise FileNotFoundError(f"Environment directory {env_dir} does not exist.")
    return read_env_file(os.path.join(env_dir, ".env"))


def kubectl_exec_psql(namespace, admin_user, admin_password, sql, database=None):
    parts = [
        f"PGPASSWORD={shlex.quote(admin_password)}",
        "psql",
        "-U",
        shlex.quote(admin_user),
    ]
    if database:
        parts.extend(["-d", shlex.quote(database)])
    parts.extend(["-c", shlex.quote(sql)])
    inner = " ".join(parts)
    execute_cli_command(
        "minikube kubectl -- exec postgresql-0 -n " f"{shlex.quote(namespace)} -- bash -c {shlex.quote(inner)}"
    )


def create_database_if_missing(
    namespace: str,
    admin_user: str,
    admin_password: str,
    db_name: str,
    app_user: str,
):
    quoted_db = quote_pg_identifier(db_name)
    safe_db_name = db_name.replace("'", "''")
    create_sql = (
        "DO $$\n"
        "BEGIN\n"
        f"  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '{safe_db_name}') THEN\n"
        f"    CREATE DATABASE {quoted_db} OWNER {app_user};\n"
        "  END IF;\n"
        "END\n"
        "$$;"
    )
    kubectl_exec_psql(namespace, admin_user, admin_password, create_sql)


def grant_database_privileges(
    namespace: str,
    admin_user: str,
    admin_password: str,
    db_name: str,
    app_user: str,
):
    quoted_db = quote_pg_identifier(db_name)

    kubectl_exec_psql(
        namespace,
        admin_user,
        admin_password,
        (f"ALTER DATABASE {quoted_db} OWNER TO {app_user}; " f"GRANT CONNECT ON DATABASE {quoted_db} TO {app_user};"),
    )

    kubectl_exec_psql(
        namespace,
        admin_user,
        admin_password,
        (f"GRANT ALL ON SCHEMA public TO {app_user}; " f"ALTER SCHEMA public OWNER TO {app_user};"),
        database=db_name,
    )


def create_database(request: CreateDatabaseRequest) -> int:
    print(f'Creating database for service "{request.repository}"')

    db_to_create_credentials = get_database_credentials(request.repository, request.namespace)
    admin_credentials = get_database_admin_credentials(request.namespace)

    admin_password = admin_credentials.get("PASSWORD")
    admin_user = admin_credentials.get("USER")
    db_name = db_to_create_credentials.get("NAME")
    app_user = db_to_create_credentials.get("USER")

    if not all([admin_password, admin_user, db_name, app_user]):
        raise ValueError("Missing required database credentials (admin USER/PASSWORD, app NAME/USER).")

    print(f'Creating database "{db_name}" with owner "{app_user}" (if not exists)...')
    create_database_if_missing(request.namespace, admin_user, admin_password, db_name, app_user)

    print(f'Granting privileges on "{db_name}" to "{app_user}"...')
    grant_database_privileges(request.namespace, admin_user, admin_password, db_name, app_user)

    print(f'Database "{db_name}" is ready in namespace "{request.namespace}".')
    print(f"To connect, use: {db_to_create_credentials}")
    print("Re-run this script safely on existing databases to fix PG15+ public schema permissions.")
    return 0
