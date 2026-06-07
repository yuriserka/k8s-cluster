import os
import uuid
from datetime import datetime, timezone

from k8s_cluster.commands.pipeline.loader import load_pipeline_file, parse_service_args, parse_step_args
from k8s_cluster.commands.pipeline.steps.credentials import handle_credentials_step
from k8s_cluster.commands.pipeline.steps.install import handle_install_step
from k8s_cluster.commands.pipeline.steps.migration import handle_database_migration_step
from k8s_cluster.commands.pipeline.steps.publish import handle_publish_step
from k8s_cluster.commands.pipeline.steps.services import handle_service
from k8s_cluster.commands.pipeline.steps.shell import run_shell_step
from k8s_cluster.paths import REPO_ROOT, SCRIPT_DIR
from k8s_cluster.utils.shell import execute_cli_command


def finish_pipeline(exit_code: int, tempfolder: str, running_services: list):
    print(f'Pipeline {"finished" if exit_code == 0 else "failed"}')
    for service_id in running_services:
        execute_cli_command(f"docker rm -f -v {service_id}")

    os.chdir(SCRIPT_DIR)
    execute_cli_command(f"rm -r {tempfolder}")
    exit(exit_code)


STEP_HANDLERS = {
    "database_migration": lambda args, path, pipeline_id, started: handle_database_migration_step(args, path),
    "credentials": lambda args, path, pipeline_id, started: handle_credentials_step(args, path),
    "install": lambda args, path, pipeline_id, started: handle_install_step(args, path, pipeline_id, started),
    "publish": lambda args, path, pipeline_id, started: handle_publish_step(args, path),
}


def run_pipeline(repository: str) -> None:
    print('echo "Pipeline started"')

    tempfolder = os.path.join(SCRIPT_DIR, f"tmp-{repository}-pipeline")
    app_source = os.path.join(REPO_ROOT, "apps", repository)
    gitignore = os.path.join(app_source, ".gitignore")
    execute_cli_command(f"rsync -r {app_source}/ {tempfolder}/ --exclude-from={gitignore}")
    pipe = load_pipeline_file(os.path.join(tempfolder, ".pipeline"))
    os.chdir(tempfolder)

    pipeline_id = str(uuid.uuid4())
    pipeline_started_at = datetime.now(timezone.utc).isoformat()
    print(f"Pipeline id: {pipeline_id} (started at {pipeline_started_at})")

    services = pipe.get("services", {})
    running_services = []
    for service_name, service_args in services.items():
        running_service_id, exit_code = handle_service(
            service_name, repository, parse_service_args(service_args), tempfolder
        )
        if exit_code != 0:
            finish_pipeline(exit_code, tempfolder, running_services)
        else:
            running_services.append(running_service_id)

    steps = pipe.get("steps", {})
    for step_name, step_args in steps.items():
        print(f'processing step: "{step_name}" in directory "{os.getcwd()}"')
        kind = step_args.get("kind")
        processor = STEP_HANDLERS.get(kind)
        if processor:
            parsed = parse_step_args(kind, step_args)
            exit_code = processor(parsed, tempfolder, pipeline_id, pipeline_started_at)
            if exit_code != 0:
                finish_pipeline(exit_code, tempfolder, running_services)
        else:
            cmds = step_args.get("cmd", [])
            for cmd in cmds:
                exit_code = run_shell_step(cmd, step_name)
                if exit_code != 0:
                    finish_pipeline(exit_code, tempfolder, running_services)

    finish_pipeline(0, tempfolder, running_services)
