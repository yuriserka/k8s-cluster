import os
import shlex

import typer

from cli_common import exit_on_failure, make_cli_app
from repo_paths import REPO_ROOT

app = make_cli_app()


def read_env_file(env_file: str):
    if not os.path.isfile(env_file):
        raise FileNotFoundError(f"Environment file {env_file} does not exist.")

    all_secrets = {}
    with open(env_file) as secrets_file:
        lines = secrets_file.readlines()
        for line in lines:
            key, value = line.split("=")
            all_secrets[f"{key.upper()}"] = value.strip()

    return all_secrets


def get_database_admin_credentials(namespace: str):
    env_dir = os.path.join(REPO_ROOT, "resources", "vault", "_admin", "database", namespace)
    if not os.path.isdir(env_dir):
        raise FileNotFoundError(f"Environment directory {env_dir} does not exist.")
    return read_env_file(os.path.join(env_dir, ".env"))


def get_database_credentials(repository: str, namespace: str):
    env_dir = os.path.join(REPO_ROOT, "resources", "vault", repository, "database", namespace)
    if not os.path.isdir(env_dir):
        raise FileNotFoundError(f"Environment directory {env_dir} does not exist.")

    return read_env_file(os.path.join(env_dir, ".env"))


def execute_cli_command(command: str):
    print(f"Executing command: {command}")
    return os.system(command)


def quote_pg_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


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
        "minikube kubectl -- exec -it postgresql-0 -n " f"{shlex.quote(namespace)} -- bash -c {shlex.quote(inner)}"
    )


def create_database_if_missing(
    namespace: str,
    admin_user: str,
    admin_password: str,
    db_name: str,
    app_user: str,
):
    quoted_db = quote_pg_identifier(db_name)
    create_sql = f"CREATE DATABASE {quoted_db} OWNER {app_user};"
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


def main(repository: str, namespace: str) -> int:
    print(f'Creating database for service "{repository}"')

    db_to_create_credentials = get_database_credentials(repository, namespace)
    admin_credentials = get_database_admin_credentials(namespace)

    admin_password = admin_credentials.get("PASSWORD")
    admin_user = admin_credentials.get("USER")
    db_name = db_to_create_credentials.get("NAME")
    app_user = db_to_create_credentials.get("USER")

    if not all([admin_password, admin_user, db_name, app_user]):
        raise ValueError("Missing required database credentials (admin USER/PASSWORD, app NAME/USER).")

    print(f'Creating database "{db_name}" with owner "{app_user}" (if not exists)...')
    create_database_if_missing(namespace, admin_user, admin_password, db_name, app_user)

    print(f'Granting privileges on "{db_name}" to "{app_user}"...')
    grant_database_privileges(namespace, admin_user, admin_password, db_name, app_user)

    print(f'Database "{db_name}" is ready in namespace "{namespace}".')
    print(f"To connect, use: {db_to_create_credentials}")
    print("Re-run this script safely on existing databases to fix PG15+ public schema permissions.")
    return 0


@app.command()
def cli(
    namespace: str = typer.Option(..., help="Kubernetes namespace (e.g. dev)"),
    repository: str = typer.Option(..., help="App folder under apps/"),
) -> None:
    try:
        exit_code = main(repository, namespace)
    except (FileNotFoundError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    exit_on_failure(exit_code, "")


if __name__ == "__main__":
    app()
