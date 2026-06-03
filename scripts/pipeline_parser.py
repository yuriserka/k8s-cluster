from typing import NamedTuple
import json
import shlex
import time
import yaml
import os
from datetime import datetime

from repo_paths import REPO_ROOT, SCRIPT_DIR

DEFAULT_POSTGRES_SERVICE = 'postgresql'
DEFAULT_POSTGRES_PORT = '5432'
POSTGRES_READY_TIMEOUT_SECONDS = 120


class ServiceArgs(NamedTuple):
    image: str
    image_env_vars: dict
    image_port_map: str
    env_vars: dict
    output_file: str


class DatabaseMigrationStepArgs(NamedTuple):
    kind: str
    env: str
    repository: str
    image_repo: str
    cmd: list[str]


class CredentialsStepArgs(NamedTuple):
    kind: str
    path: str
    output_file: str


class InstallStepArgs(NamedTuple):
    kind: str
    application: str
    params_file: str
    repo: str
    env: str


class PublishStepArgs(NamedTuple):
    kind: str
    repo: str
    env: str
    dockerfile: str
    build_args: dict = {}


def execute_cli_command(command: str):
    print(f'Executing command: {command}')
    return os.system(command)


def finish_pipeline(exit_code: int, tempfolder: str, running_services: list):
    print(f'Pipeline {"finished" if exit_code == 0 else "failed"}')
    for service_id in running_services:
        execute_cli_command(f'docker rm -f -v {service_id}')

    os.chdir(SCRIPT_DIR)
    execute_cli_command(f'rm -r {tempfolder}')
    exit(exit_code)


def wait_for_docker_postgres(container_id: str, pg_user: str, timeout_seconds: int = 60) -> int:
    for second in range(timeout_seconds):
        exit_code = execute_cli_command(
            f'docker exec {shlex.quote(container_id)} '
            f'pg_isready -U {shlex.quote(pg_user)} -q'
        )
        if exit_code == 0:
            if second > 0:
                print(f'PostgreSQL ready after {second + 1}s')
            return 0
        time.sleep(1)

    print(
        f'PostgreSQL in container "{container_id}" did not become ready '
        f'within {timeout_seconds}s.'
    )
    return 1


def handle_service(service_name: str, repository: str, args: ServiceArgs, temp_folder_path: str):
    print(f'Starting service for {repository} with args: {args}')
    container_id = f'{repository}-{service_name}'
    image_env_vars = ' '.join(
        [f'-e {key}={value}' for key, value in args.image_env_vars.items()],
    )
    credentials_path = os.path.join(
        temp_folder_path, args.output_file.lstrip('./')
    )
    write_secrets_to_file(args.env_vars, credentials_path)

    execute_cli_command(f'docker rm -f {container_id} >/dev/null 2>&1')

    exit_code = execute_cli_command(
        'docker run --pull=always -d '
        f'--name {container_id} -p {args.image_port_map} {image_env_vars} {args.image}'
    )
    if exit_code != 0:
        return container_id, exit_code

    pg_user = args.image_env_vars.get('POSTGRES_USER', 'postgres')
    return container_id, wait_for_docker_postgres(container_id, pg_user)


def handle_install_step(args: InstallStepArgs, temp_folder_path: str):
    print('Installing app with args:', args)
    install_script = os.path.join(SCRIPT_DIR, 'install_app.py')
    return execute_cli_command(
        f'python {install_script} -r {args.repo} -a {args.application} '
        f'-e {args.params_file} -p {temp_folder_path} -n {args.env} -t {args.env}'
    )


def handle_publish_step(args: PublishStepArgs, temp_folder_path: str):
    print('Publishing app with args:', args)
    publish_script = os.path.join(SCRIPT_DIR, 'publish_app.py')
    build_args_flag = ''
    if args.build_args:
        build_args_flag = f'-b {shlex.quote(json.dumps(args.build_args))} '
    return execute_cli_command(
        f'python {publish_script} -r {args.repo} -d {args.dockerfile} '
        f'{build_args_flag}-p {temp_folder_path} -n {args.env} -k -t {args.env}'
    )


def write_secrets_to_file(secrets: dict, output_file: str):
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_file, 'w') as file:
        for key, value in secrets.items():
            file.write(f'{key}={value}\n')


def handle_credentials_step(args: CredentialsStepArgs, temp_folder_path: str):
    print('Getting credentials with args:', args)
    resource, target, namespace = args.path.split(':')
    all_secrets = {}
    vault_root = os.path.join(REPO_ROOT, 'resources', 'vault', target)
    resource_directories = os.listdir(vault_root)
    for resource_name in resource_directories:
        if resource_name != resource:
            continue
        env_dir = os.path.join(vault_root, resource_name, namespace)
        if not os.path.isdir(env_dir):
            continue

        with open(os.path.join(env_dir, '.env')) as secrets_file:
            lines = secrets_file.readlines()
            for line in lines:
                key, value = line.split('=')
                all_secrets[f"{resource_name.upper()}_{key.upper()}"] = value.strip()

    credentials_path = os.path.join(
        temp_folder_path, args.output_file.lstrip('./')
    )
    write_secrets_to_file(all_secrets, credentials_path)

    return 0


def read_vault_database_secrets(repository: str, namespace: str) -> dict:
    env_file = os.path.join(
        REPO_ROOT, 'resources', 'vault', repository, 'database', namespace, '.env'
    )
    secrets = {}
    with open(env_file) as secrets_file:
        for line in secrets_file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            secrets[key.upper()] = value.strip()
    return secrets


def resolve_cluster_database_host(namespace: str, secrets: dict) -> str:
    """Kubernetes Service DNS name for in-cluster clients (not minikube service URL)."""
    host = secrets.get('CLUSTER_HOST', DEFAULT_POSTGRES_SERVICE)
    exit_code = execute_cli_command(
        'minikube kubectl -- get svc '
        f'{shlex.quote(host)} -n {shlex.quote(namespace)} >/dev/null 2>&1'
    )
    if exit_code != 0:
        raise RuntimeError(
            f'PostgreSQL service "{host}" not found in namespace "{namespace}". '
            'Install infra (helm postgresql) or set CLUSTER_HOST in vault database .env.'
        )
    return host


def wait_for_postgresql_ready(namespace: str) -> int:
    return execute_cli_command(
        'minikube kubectl -- wait --for=condition=ready '
        f'pod/{DEFAULT_POSTGRES_SERVICE}-0 -n {shlex.quote(namespace)} '
        f'--timeout={POSTGRES_READY_TIMEOUT_SECONDS}s'
    )


def load_cluster_database_env(repository: str, namespace: str) -> dict:
    secrets = read_vault_database_secrets(repository, namespace)
    cluster_host = resolve_cluster_database_host(namespace, secrets)

    return {
        'DATABASE_USER': secrets['USER'],
        'DATABASE_PASSWORD': secrets['PASSWORD'],
        'DATABASE_NAME': secrets['NAME'],
        'DATABASE_PORT': secrets.get('PORT', DEFAULT_POSTGRES_PORT),
        'DATABASE_HOST': cluster_host,
    }


def run_in_cluster_migration_command(
    namespace: str,
    image: str,
    env_vars: dict,
    command_argv: list[str],
    run_id: str,
) -> int:
    overrides = {
        'spec': {
            'containers': [{
                'name': 'migrate',
                'image': image,
                'imagePullPolicy': 'Never',
                'env': [
                    {'name': key, 'value': value}
                    for key, value in env_vars.items()
                ],
                'command': command_argv,
            }],
        },
    }
    pod_name = f'migrate-{run_id}'
    cmd = (
        f'minikube kubectl -- run {shlex.quote(pod_name)} '
        f'--rm -i --restart=Never -n {shlex.quote(namespace)} '
        f'--image={shlex.quote(image)} '
        f'--overrides={shlex.quote(json.dumps(overrides))}'
    )
    return execute_cli_command(cmd)


def handle_database_migration_step(args: DatabaseMigrationStepArgs, temp_folder_path: str):
    print('Migrating database in cluster with args:', args)

    exit_code = wait_for_postgresql_ready(args.env)
    if exit_code != 0:
        print(
            f'PostgreSQL is not ready in namespace "{args.env}" '
            f'(waited {POSTGRES_READY_TIMEOUT_SECONDS}s for pod/{DEFAULT_POSTGRES_SERVICE}-0).'
        )
        return exit_code

    create_script = os.path.join(SCRIPT_DIR, 'create_database.py')
    exit_code = execute_cli_command(
        f'python {create_script} -n {args.env} -r {args.repository}'
    )
    if exit_code != 0:
        return exit_code

    database_env = load_cluster_database_env(args.repository, args.env)
    image = f'{args.image_repo}-{args.env}:{args.env}'
    run_id = datetime.now().strftime('%H%M%S%f')

    for index, command in enumerate(args.cmd):
        command_argv = shlex.split(command)
        exit_code = run_in_cluster_migration_command(
            args.env,
            image,
            database_env,
            command_argv,
            f'{run_id}-{index}',
        )
        if exit_code != 0:
            return exit_code

    return 0


step_kinds_processor = {
    'database_migration': lambda args, path: handle_database_migration_step(DatabaseMigrationStepArgs(**args), path),
    'credentials': lambda args, path: handle_credentials_step(CredentialsStepArgs(**args), path),
    'install': lambda args, path: handle_install_step(InstallStepArgs(**args), path),
    'publish': lambda args, path: handle_publish_step(PublishStepArgs(**args), path),
}


def read_file(file_path: str):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def main(repository: str):
    print('echo "Pipeline started"')

    tempfolder = os.path.join(SCRIPT_DIR, f'tmp-{repository}-pipeline')
    app_source = os.path.join(REPO_ROOT, 'apps', repository)
    gitignore = os.path.join(app_source, '.gitignore')
    execute_cli_command(
        f'rsync -r {app_source}/ {tempfolder}/ --exclude-from={gitignore}'
    )
    pipe = read_file(os.path.join(tempfolder, '.pipeline'))
    os.chdir(tempfolder)

    services = pipe.get('services', {})
    running_services = []
    for service_name, service_args in services.items():
        running_service_id, exit_code = handle_service(
            service_name, repository, ServiceArgs(**service_args), tempfolder
        )
        if exit_code != 0:
            finish_pipeline(exit_code, tempfolder, running_services)
        else:
            running_services.append(running_service_id)

    steps = pipe.get('steps', {})
    for step_name, step_args in steps.items():
        print(
            f'processing step: "{step_name}" in directory "{os.getcwd()}"'
        )
        kind = step_args.get('kind')
        processor = step_kinds_processor.get(kind)
        if processor:
            exit_code = processor(step_args, tempfolder)
            if exit_code != 0:
                finish_pipeline(exit_code, tempfolder, running_services)
        else:
            cmds = step_args.get('cmd', [])
            for cmd in cmds:
                exit_code = execute_cli_command(cmd)
                if exit_code != 0:
                    finish_pipeline(exit_code, tempfolder, running_services)

    finish_pipeline(0, tempfolder, running_services)


if __name__ == '__main__':
    args = os.sys.argv[1:]
    repository = args[0]

    os.chdir(SCRIPT_DIR)
    main(repository)
