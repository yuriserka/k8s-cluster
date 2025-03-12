from functools import reduce
from typing import NamedTuple
import yaml
import os
from datetime import datetime

root_dir = os.getcwd()
pipeline_tag = datetime.today().strftime('%Y.%m.%d.%H.%M.%S')


class ServiceArgs(NamedTuple):
    image: str
    image_env_vars: dict
    image_port_map: str
    env_vars: dict
    output_file: str


class DatabaseMigrationStepArgs(NamedTuple):
    kind: str
    env: str
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


def execute_cli_command(command: str):
    print(f'Executing command: {command}')
    return os.system(command)


def finish_pipeline(exit_code: int, tempfolder: str, running_services: list):
    print(f'Pipeline {"finished" if exit_code == 0 else "failed"}')
    for service_id in running_services:
        execute_cli_command(f'docker rm -f -v {service_id}')

    os.chdir(root_dir)
    execute_cli_command(f'rm -r {tempfolder}')
    exit(exit_code)


def handle_service(service_name: str, repository: str, args: ServiceArgs, temp_folder_path: str):
    print(f'Starting service for {repository} with args: {args}')
    container_id = f'{repository}-{service_name}'
    image_env_vars = ' '.join(
        [f'-e {key}={value}' for key, value in args.image_env_vars.items()],
    )
    write_secrets_to_file(args.env_vars, args.output_file)

    return (
        container_id,
        execute_cli_command(
            'docker run --pull=always -d '
            f'--name {container_id} -p {args.image_port_map} {image_env_vars} {args.image}'
        )
    )


def handle_install_step(args: InstallStepArgs, temp_folder_path: str):
    print('Installing app with args:', args)
    os.chdir(root_dir)
    return execute_cli_command(
        f'python install_app.py -r {args.repo} -a {args.application} '
        f'-e {args.params_file} -p {temp_folder_path} -n {args.env} -t {pipeline_tag}'
    )


def handle_publish_step(args: PublishStepArgs, temp_folder_path: str):
    print('Publishing app with args:', args)
    os.chdir(root_dir)
    return execute_cli_command(
        f'python publish_app.py -r {args.repo} -d {args.dockerfile} '
        f'-p {temp_folder_path} -n {args.env} -k -t {pipeline_tag}'
    )


def write_secrets_to_file(secrets: dict, output_file: str):
    with open(output_file, 'w') as file:
        for key, value in secrets.items():
            file.write(f'{key}={value}\n')


def handle_credentials_step(args: CredentialsStepArgs, temp_folder_path: str):
    print('Getting credentials with args:', args)
    resource, target, namespace = args.path.split(':')
    all_secrets = {}
    os.chdir(root_dir)
    resource_directories = os.listdir(f'resources/vault/{target}')
    for resource in resource_directories:
        env_dir = f'resources/vault/{target}/{resource}/{namespace}'
        if not os.path.isdir(env_dir):
            continue

        with open(f'{env_dir}/.env') as secrets_file:
            lines = secrets_file.readlines()
            for line in lines:
                key, value = line.split('=')
                all_secrets[f"{resource.upper()}_{key.upper()}"] = value.strip()

    write_secrets_to_file(
        all_secrets, f'{temp_folder_path}/{args.output_file}')

    return 0


def handle_database_migration_step(args: DatabaseMigrationStepArgs, temp_folder_path: str):
    print('Migrating database with args:', args)
    os.chdir(temp_folder_path)
    return reduce(
        lambda acc, cmd: acc + execute_cli_command(cmd),
        args.cmd,
        0,
    )


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

    tempfolder = f'tmp-{repository}-pipeline'
    execute_cli_command(
        f'rsync -r ./apps/{repository}/ {tempfolder}/ --exclude-from=./apps/{repository}/.gitignore'
    )
    pipe = read_file(f'{tempfolder}/.pipeline')
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

    main(repository)
