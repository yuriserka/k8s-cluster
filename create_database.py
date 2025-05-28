import os


def read_env_file(env_file: str):
    if not os.path.isfile(env_file):
        raise FileNotFoundError(f'Environment file {env_file} does not exist.')

    all_secrets = {}
    with open(env_file) as secrets_file:
        lines = secrets_file.readlines()
        for line in lines:
            key, value = line.split('=')
            all_secrets[f"{key.upper()}"] = value.strip()

    return all_secrets


def get_database_admin_credentials(namespace: str):
    env_dir = f'resources/vault/_admin/database/{namespace}'
    if not os.path.isdir(env_dir):
        raise FileNotFoundError(
            f'Environment directory {env_dir} does not exist.')
    return read_env_file(f'{env_dir}/.env')


def get_database_credentials(repository: str, namespace: str):
    env_dir = f'resources/vault/{repository}/database/{namespace}'
    if not os.path.isdir(env_dir):
        raise FileNotFoundError(
            f'Environment directory {env_dir} does not exist.')

    return read_env_file(f'{env_dir}/.env')


def execute_cli_command(command: str):
    print(f'Executing command: {command}')
    return os.system(command)


def main(repository: str, namespace: str):
    print(f'Creating database for service "{repository}"')

    db_to_create_credentials = get_database_credentials(repository, namespace)
    admin_credentials = get_database_admin_credentials(namespace)

    password = admin_credentials.get('PASSWORD')
    user = admin_credentials.get('USER')
    database = f"\\\"{db_to_create_credentials.get('NAME')}\\\""

    create_db_stmt = f"""PGPASSWORD={password} psql -U {user} -c 'CREATE DATABASE {database};'"""
    execute_cli_command(
        f'minikube kubectl -- exec -it postgresql-0 -n {namespace} -- bash -c "{create_db_stmt}"'
    )

    print(
        f'Database "{db_to_create_credentials.get("NAME")}" created successfully in namespace "{namespace}".')
    print(
        f"to connect to the database, use the following credentials: {db_to_create_credentials}")


if __name__ == '__main__':
    args = os.sys.argv[1:]

    if "-n" not in args:
        print("Namespace is required to install the app. Use -n flag to specify the namespace.")
        exit(1)

    if "-r" not in args:
        print("Repository is required to install the app. Use -r flag to specify the repository.")
        exit(1)

    namespace = args[args.index("-n") + 1]
    repository = args[args.index("-r") + 1]

    main(repository, namespace)
