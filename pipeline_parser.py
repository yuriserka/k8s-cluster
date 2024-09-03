from typing import NamedTuple
import yaml
import os

root_dir = os.getcwd()


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


def finish_pipeline(exit_code: int, tempfolder: str):
    print(f'Pipeline {"finished" if exit_code == 0 else "failed"}')
    os.chdir(root_dir)
    os.system(f'rm -r {tempfolder}')
    exit(exit_code)


def handle_install_step(args: InstallStepArgs, temp_folder_path: str):
    print('Installing app with args:', args)
    os.chdir(root_dir)
    return os.system(
        f'python install_app.py -r {args.repo} -a {args.application} '
        f'-e {args.params_file} -p {temp_folder_path} -n {args.env}'
    )


def handle_publish_step(args: PublishStepArgs, temp_folder_path: str):
    print('Publishing app with args:', args)
    os.chdir(root_dir)
    return os.system(
        f'python publish_app.py -r {args.repo} -d {args.dockerfile} -p {temp_folder_path} -n {args.env}'
    )


step_kinds_processor = {
    'install': lambda args, path: handle_install_step(InstallStepArgs(**args), path),
    'publish': lambda args, path: handle_publish_step(PublishStepArgs(**args), path),
}


def read_file(file_path: str):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def main(repository: str):
    print('echo "Pipeline started"')

    tempfolder = f'tmp-{repository}-pipeline'
    os.system(
        f'rsync -r ./apps/{repository}/ {tempfolder}/ --exclude-from=./apps/{repository}/.gitignore'
    )
    pipe = read_file(f'{tempfolder}/.pipeline')
    os.chdir(tempfolder)

    steps = pipe['steps']
    for step_name, step_args in steps.items():
        print(
            f'processing step: "{step_name}" in directory "{os.getcwd()}"'
        )
        kind = step_args.get('kind')
        processor = step_kinds_processor.get(kind)
        if processor:
            exit_code = processor(step_args, tempfolder)
            if exit_code != 0:
                finish_pipeline(exit_code, tempfolder)
        else:
            cmds = step_args.get('cmd', [])
            for cmd in cmds:
                exit_code = os.system(cmd)
                if exit_code != 0:
                    finish_pipeline(exit_code, tempfolder)

    finish_pipeline(0, tempfolder)


if __name__ == '__main__':
    args = os.sys.argv[1:]
    repository = args[0]

    main(repository)
