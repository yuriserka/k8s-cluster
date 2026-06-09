import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from k8s_cluster.commands.pipeline.loader import (
    load_pipeline_file,
    parse_service_args,
    parse_step_args,
    strip_step_metadata,
)
from k8s_cluster.commands.pipeline.log import (
    log_pipeline_finish,
    log_pipeline_start,
    log_service_start,
    log_step_end,
    log_step_start,
    log_wave_start,
    summarize_service,
    summarize_step,
)
from k8s_cluster.commands.pipeline.planner import PipelinePlanError, build_execution_plan
from k8s_cluster.commands.pipeline.steps.clone import handle_clone_step
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
    if os.path.isdir(tempfolder):
        execute_cli_command(f"rm -r {tempfolder}")
    exit(exit_code)


STEP_HANDLERS = {
    "clone": lambda args, path, repository, pipeline_id, started: handle_clone_step(repository, path),
    "database_migration": lambda args, path, repository, pipeline_id, started: handle_database_migration_step(
        args, path
    ),
    "credentials": lambda args, path, repository, pipeline_id, started: handle_credentials_step(args, path),
    "install": lambda args, path, repository, pipeline_id, started: handle_install_step(
        args, path, pipeline_id, started
    ),
    "publish": lambda args, path, repository, pipeline_id, started: handle_publish_step(args, path),
}


def _run_single_step(
    step_name: str,
    step_args: dict,
    *,
    repository: str,
    tempfolder: str,
    pipeline_id: str,
    pipeline_started_at: str,
    step_index: int,
    total_steps: int,
    wave_index: int,
    log_lock: threading.Lock,
) -> int:
    handler_args = strip_step_metadata(step_args)
    kind = handler_args.get("kind") or "shell"
    with log_lock:
        log_step_start(
            step_index,
            total_steps,
            step_name,
            kind,
            summarize_step(step_name, step_args),
            wave_index=wave_index,
        )

    step_started_at = time.monotonic()
    processor = STEP_HANDLERS.get(handler_args.get("kind"))
    if processor:
        parsed = parse_step_args(handler_args.get("kind"), handler_args)
        exit_code = processor(parsed, tempfolder, repository, pipeline_id, pipeline_started_at)
    else:
        exit_code = 0
        for cmd in handler_args.get("cmd", []):
            exit_code = run_shell_step(cmd, step_name)
            if exit_code != 0:
                break

    with log_lock:
        log_step_end(
            step_index,
            total_steps,
            step_name,
            exit_code,
            time.monotonic() - step_started_at,
            wave_index=wave_index,
        )
    return exit_code


def _execute_wave(
    wave: list[str],
    steps: dict[str, dict],
    *,
    repository: str,
    tempfolder: str,
    pipeline_id: str,
    pipeline_started_at: str,
    wave_index: int,
    step_indices: dict[str, int],
    total_steps: int,
    log_lock: threading.Lock,
) -> int:
    if len(wave) == 1:
        step_name = wave[0]
        return _run_single_step(
            step_name,
            steps[step_name],
            repository=repository,
            tempfolder=tempfolder,
            pipeline_id=pipeline_id,
            pipeline_started_at=pipeline_started_at,
            step_index=step_indices[step_name],
            total_steps=total_steps,
            wave_index=wave_index,
            log_lock=log_lock,
        )

    first_failure = 0
    with ThreadPoolExecutor(max_workers=len(wave)) as executor:
        futures = {
            executor.submit(
                _run_single_step,
                step_name,
                steps[step_name],
                repository=repository,
                tempfolder=tempfolder,
                pipeline_id=pipeline_id,
                pipeline_started_at=pipeline_started_at,
                step_index=step_indices[step_name],
                total_steps=total_steps,
                wave_index=wave_index,
                log_lock=log_lock,
            ): step_name
            for step_name in wave
        }
        for future in as_completed(futures):
            exit_code = future.result()
            if exit_code != 0 and first_failure == 0:
                first_failure = exit_code
    return first_failure


def _run_waves(
    waves: list[list[str]],
    steps: dict[str, dict],
    *,
    repository: str,
    tempfolder: str,
    pipeline_id: str,
    pipeline_started_at: str,
    step_indices: dict[str, int],
    total_steps: int,
    log_lock: threading.Lock,
    start_wave_index: int = 0,
) -> int:
    for offset, wave in enumerate(waves):
        wave_index = start_wave_index + offset
        log_wave_start(wave_index, wave)
        exit_code = _execute_wave(
            wave,
            steps,
            repository=repository,
            tempfolder=tempfolder,
            pipeline_id=pipeline_id,
            pipeline_started_at=pipeline_started_at,
            wave_index=wave_index,
            step_indices=step_indices,
            total_steps=total_steps,
            log_lock=log_lock,
        )
        if exit_code != 0:
            return exit_code
    return 0


def run_pipeline(repository: str) -> None:
    pipeline_started_at_monotonic = time.monotonic()
    tempfolder = os.path.join(SCRIPT_DIR, f"tmp-{repository}-pipeline")
    pipeline_file = os.path.join(REPO_ROOT, "apps", repository, ".pipeline")

    try:
        pipe = load_pipeline_file(pipeline_file)
        steps = pipe.get("steps", {})
        waves = build_execution_plan(steps)
    except PipelinePlanError as error:
        print(f"Pipeline plan error: {error}")
        exit(1)

    pipeline_id = str(uuid.uuid4())
    pipeline_started_at = datetime.now(timezone.utc).isoformat()
    log_pipeline_start(repository, pipeline_id, pipeline_started_at, tempfolder)

    flat_steps = [step_name for wave in waves for step_name in wave]
    step_indices = {step_name: index for index, step_name in enumerate(flat_steps, start=1)}
    total_steps = len(flat_steps)
    log_lock = threading.Lock()

    clone_exit_code = _run_waves(
        [waves[0]],
        steps,
        repository=repository,
        tempfolder=tempfolder,
        pipeline_id=pipeline_id,
        pipeline_started_at=pipeline_started_at,
        step_indices=step_indices,
        total_steps=total_steps,
        log_lock=log_lock,
        start_wave_index=0,
    )
    if clone_exit_code != 0:
        finish_pipeline(
            clone_exit_code,
            tempfolder,
            [],
            pipeline_started_at_monotonic=pipeline_started_at_monotonic,
        )

    os.chdir(tempfolder)

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
        running_services.append(running_service_id)

    if len(waves) > 1:
        exit_code = _run_waves(
            waves[1:],
            steps,
            repository=repository,
            tempfolder=tempfolder,
            pipeline_id=pipeline_id,
            pipeline_started_at=pipeline_started_at,
            step_indices=step_indices,
            total_steps=total_steps,
            log_lock=log_lock,
            start_wave_index=1,
        )
        if exit_code != 0:
            finish_pipeline(
                exit_code,
                tempfolder,
                running_services,
                pipeline_started_at_monotonic=pipeline_started_at_monotonic,
            )

    finish_pipeline(0, tempfolder, running_services, pipeline_started_at_monotonic=pipeline_started_at_monotonic)
