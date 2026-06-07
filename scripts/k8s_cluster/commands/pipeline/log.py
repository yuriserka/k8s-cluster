SEPARATOR_MAJOR = "=" * 72
SEPARATOR_MINOR = "-" * 72
DETAIL_PREFIX = "  "


def _truncate(text: str, max_length: int = 80) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _print_block(lines: list[str]) -> None:
    for line in lines:
        print(line)


def log_pipeline_start(repository: str, pipeline_id: str, started_at: str, work_dir: str) -> None:
    _print_block(
        [
            SEPARATOR_MAJOR,
            f"PIPELINE START: {repository}",
            f"  pipeline_id: {pipeline_id}",
            f"  started_at:  {started_at}",
            f"  work_dir:    {work_dir}",
            SEPARATOR_MAJOR,
        ]
    )


def log_pipeline_finish(exit_code: int, elapsed_seconds: float) -> None:
    status = "SUCCESS" if exit_code == 0 else f"FAILED (exit {exit_code})"
    _print_block(
        [
            SEPARATOR_MAJOR,
            f"PIPELINE {status}  finished in {elapsed_seconds:.1f}s",
            SEPARATOR_MAJOR,
        ]
    )


def log_service_start(index: int, total: int, name: str, summary_lines: list[str]) -> None:
    header = f"SERVICE {index}/{total}: {name}"
    lines = [SEPARATOR_MAJOR, header]
    for summary_line in summary_lines:
        lines.append(f"{DETAIL_PREFIX}{summary_line}")
    lines.append(SEPARATOR_MAJOR)
    _print_block(lines)


def log_step_start(index: int, total: int, step_name: str, kind: str, summary_lines: list[str]) -> None:
    header = f"STEP {index}/{total}: {step_name}  |  kind: {kind}"
    lines = [SEPARATOR_MAJOR, header]
    for summary_line in summary_lines:
        lines.append(f"{DETAIL_PREFIX}{summary_line}")
    lines.append(SEPARATOR_MAJOR)
    _print_block(lines)


def log_step_detail(message: str) -> None:
    print(f"{DETAIL_PREFIX}{message}")


def log_step_end(index: int, total: int, step_name: str, exit_code: int, elapsed_seconds: float) -> None:
    if exit_code == 0:
        status = f"finished in {elapsed_seconds:.1f}s  (exit 0)"
    else:
        status = f"FAILED in {elapsed_seconds:.1f}s  (exit {exit_code})"
    _print_block(
        [
            SEPARATOR_MINOR,
            f"STEP {index}/{total}: {step_name}  {status}",
            SEPARATOR_MINOR,
        ]
    )


def summarize_service(service_args: dict) -> list[str]:
    lines = [
        f"image: {service_args.get('image', '')}",
        f"ports: {service_args.get('image_port_map', '')}",
        f"output_file: {service_args.get('output_file', '')}",
    ]
    return lines


def summarize_step(step_name: str, step_args: dict) -> list[str]:
    kind = step_args.get("kind")
    if kind is None:
        cmds = step_args.get("cmd", [])
        lines = [f"commands: {len(cmds)}"]
        if cmds:
            lines.append(f"first: {_truncate(cmds[0])}")
        return lines

    if kind == "publish":
        repo = step_args.get("repo", "")
        env = step_args.get("env", "")
        image = f"{repo}-{env}:{env}"
        lines = [
            f"repository: {repo}",
            f"env: {env}  |  image: {image}",
            f"dockerfile: {step_args.get('dockerfile', '')}",
        ]
        build_args = step_args.get("build_args")
        if build_args:
            lines.append(f"build_args: {build_args}")
        return lines

    if kind == "install":
        application = step_args.get("application", "")
        env = step_args.get("env", "")
        return [
            f"application: {application}",
            f"repo: {step_args.get('repo', '')}",
            f"env: {env}  |  release: {application}",
            f"params_file: {step_args.get('params_file', '')}",
        ]

    if kind == "credentials":
        return [
            f"path: {step_args.get('path', '')}",
            f"output_file: {step_args.get('output_file', '')}",
        ]

    if kind == "database_migration":
        env = step_args.get("env", "")
        image_repo = step_args.get("image_repo", "")
        cmds = step_args.get("cmd", [])
        return [
            f"repository: {step_args.get('repository', '')}",
            f"env: {env}  |  image: {image_repo}-{env}:{env}",
            f"migrate_commands: {len(cmds)}",
        ]

    return [f"kind: {kind}"]
