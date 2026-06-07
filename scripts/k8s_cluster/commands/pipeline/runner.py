import os
import time
import uuid
from datetime import datetime, timezone

from k8s_cluster.commands.pipeline.loader import load_pipeline_file, parse_service_args, parse_step_args
from k8s_cluster.commands.pipeline.log import (
    log_pipeline_finish,
    log_pipeline_start,
    log_service_start,
    log_step_end,
    log_step_start,
    summarize_service,
    summarize_step,
)
from k8s_cluster.commands.pipeline.steps.credentials import handle_credentials_step
from k8s_cluster.commands.pipeline.steps.install import handle_install_step
from k8s_cluster.commands.pipeline.steps.migration import handle_database_migration_step
from k8s_cluster.commands.pipeline.steps.publish import handle_publish_step
from k8s_cluster.commands.pipeline.steps.services import handle_service
from k8s_cluster.commands.pipeline.steps.shell import run_shell_step
from k8s_cluster.paths import REPO_ROOT, SCRIPT_DIR
from k8s_cluster.utils.shell import execute_cli_command


def finish_pipeline(
    exit_code: int,
    tempfolder: str,
    running_services: list,
    *,
    pipeline_started_at_monotonic: float,
):
    elapsed = time.monotonic() - pipeline_started_at_monotonic
    log_pipeline_finish(exit_code, elapsed)
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
    pipeline_started_at_monotonic = time.monotonic()

    tempfolder = os.path.join(SCRIPT_DIR, f"tmp-{repository}-pipeline")
    app_source = os.path.join(REPO_ROOT, "apps", repository)
    gitignore = os.path.join(app_source, ".gitignore")
    execute_cli_command(f"rsync -r {app_source}/ {tempfolder}/ --exclude-from={gitignore}")
    pipe = load_pipeline_file(os.path.join(tempfolder, ".pipeline"))
    os.chdir(tempfolder)

    pipeline_id = str(uuid.uuid4())
    pipeline_started_at = datetime.now(timezone.utc).isoformat()
    log_pipeline_start(repository, pipeline_id, pipeline_started_at, tempfolder)

    services = pipe.get("services", {})
    service_items = list(services.items())
    running_services = []
    for service_index, (service_name, service_args) in enumerate(service_items, start=1):
        log_service_start(
            service_index,
            len(service_items),
            service_name,
            summarize_service(service_args),
        )
        running_service_id, exit_code = handle_service(
            service_name, repository, parse_service_args(service_args), tempfolder
        )
        if exit_code != 0:
            finish_pipeline(
                exit_code, tempfolder, running_services, pipeline_started_at_monotonic=pipeline_started_at_monotonic
            )
        else:
            running_services.append(running_service_id)

    steps = pipe.get("steps", {})
    step_items = list(steps.items())
    total_steps = len(step_items)
    for step_index, (step_name, step_args) in enumerate(step_items, start=1):
        kind = step_args.get("kind") or "shell"
        log_step_start(
            step_index,
            total_steps,
            step_name,
            kind,
            summarize_step(step_name, step_args),
        )
        step_started_at = time.monotonic()
        processor = STEP_HANDLERS.get(step_args.get("kind"))
        if processor:
            parsed = parse_step_args(step_args.get("kind"), step_args)
            exit_code = processor(parsed, tempfolder, pipeline_id, pipeline_started_at)
        else:
            exit_code = 0
            cmds = step_args.get("cmd", [])
            for cmd in cmds:
                exit_code = run_shell_step(cmd, step_name)
                if exit_code != 0:
                    break

        log_step_end(step_index, total_steps, step_name, exit_code, time.monotonic() - step_started_at)
        if exit_code != 0:
            finish_pipeline(
                exit_code, tempfolder, running_services, pipeline_started_at_monotonic=pipeline_started_at_monotonic
            )

    finish_pipeline(0, tempfolder, running_services, pipeline_started_at_monotonic=pipeline_started_at_monotonic)
