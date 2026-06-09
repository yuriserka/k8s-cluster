class PipelinePlanError(ValueError):
    pass


def _normalize_depends_on(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise PipelinePlanError(f"depends_on must be a step name or null, got {value!r}")


def _find_clone_steps(steps: dict[str, dict]) -> list[str]:
    return [name for name, args in steps.items() if args.get("kind") == "clone"]


def _validate_clone_step(clone_name: str, step_args: dict) -> None:
    if "depends_on" in step_args and step_args.get("depends_on") is not None:
        raise PipelinePlanError(f"clone step {clone_name!r} must not define depends_on")


def _validate_non_clone_step(step_name: str, parent: str | None, steps: dict[str, dict]) -> None:
    if parent is None:
        raise PipelinePlanError(f"step {step_name!r} must define depends_on")
    if parent not in steps:
        raise PipelinePlanError(f"step {step_name!r} depends_on unknown step {parent!r}")


def _resolve_parent(step_name: str, step_args: dict, clone_name: str, steps: dict[str, dict]) -> str | None:
    if step_name == clone_name:
        _validate_clone_step(clone_name, step_args)
        return None

    if "depends_on" not in step_args:
        raise PipelinePlanError(f"step {step_name!r} must define depends_on")

    parent = _normalize_depends_on(step_args["depends_on"])
    _validate_non_clone_step(step_name, parent, steps)
    return parent


def _build_parent_graph(steps: dict[str, dict], clone_name: str) -> dict[str | None, list[str]]:
    children: dict[str | None, list[str]] = {}
    for step_name, step_args in steps.items():
        parent = _resolve_parent(step_name, step_args, clone_name, steps)
        children.setdefault(parent, []).append(step_name)
    return children


def _waves_from_children(children: dict[str | None, list[str]], step_count: int) -> list[list[str]]:
    waves: list[list[str]] = []
    current = children.get(None, [])
    if not current:
        raise PipelinePlanError("no root step found (expected kind: clone)")

    visited = 0
    while current:
        waves.append(current)
        visited += len(current)
        next_wave: list[str] = []
        for parent in current:
            next_wave.extend(children.get(parent, []))
        current = next_wave

    if visited != step_count:
        raise PipelinePlanError("cycle detected or unreachable steps in depends_on graph")

    return waves


def build_execution_plan(steps: dict[str, dict]) -> list[list[str]]:
    if not steps:
        raise PipelinePlanError("steps must not be empty")

    clone_steps = _find_clone_steps(steps)
    if len(clone_steps) != 1:
        raise PipelinePlanError(f"expected exactly one kind: clone step, found {clone_steps!r}")

    children = _build_parent_graph(steps, clone_steps[0])
    return _waves_from_children(children, len(steps))
