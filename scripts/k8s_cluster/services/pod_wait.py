import shlex
import time
from enum import Enum
from typing import Optional

from k8s_cluster.services.kubectl import (
    all_containers_ready,
    find_pod_name_by_label,
    get_failed_exit_code,
    get_pod,
    has_running_container,
    is_container_creating,
    pod_has_ready_condition,
)

DEFAULT_POSTGRES_SERVICE = "postgresql"
DEFAULT_POSTGRES_POD = "postgresql-0"
DEFAULT_KAFKA_CONTROLLER_POD = "kafka-controller-0"
DEFAULT_LOCALSTACK_RELEASE = "localstack"
DEFAULT_KAFKA_UI_RELEASE = "kafka-ui"
READY_TIMEOUT_SECONDS = 120
POD_POLL_INTERVAL_SECONDS = 5


class PodWaitState(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    PROGRESSING = "PROGRESSING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


def classify_pod_state(pod: Optional[dict], *, expect_succeeded: bool, has_seen_running: bool) -> PodWaitState:
    if pod is None:
        return PodWaitState.PENDING

    failed_exit_code = get_failed_exit_code(pod)
    if failed_exit_code is not None:
        return PodWaitState.FAILED

    phase = pod.get("status", {}).get("phase")

    if expect_succeeded and phase == "Succeeded":
        return PodWaitState.FINISHED

    if not expect_succeeded and (pod_has_ready_condition(pod) or (phase == "Running" and all_containers_ready(pod))):
        return PodWaitState.FINISHED

    if phase == "Pending" or is_container_creating(pod):
        return PodWaitState.PENDING

    if has_running_container(pod) and not all_containers_ready(pod):
        if has_seen_running:
            return PodWaitState.PROGRESSING
        return PodWaitState.STARTED

    if phase == "Running":
        return PodWaitState.PROGRESSING

    return PodWaitState.PENDING


class PodStateTracker:
    def __init__(self, label: str):
        self.label = label
        self.has_seen_running = False
        self.last_printed_state: Optional[PodWaitState] = None
        self.last_progressing_print = 0.0

    def observe(self, state: PodWaitState) -> None:
        now = time.time()
        if state == PodWaitState.STARTED:
            self.has_seen_running = True

        should_print = state != self.last_printed_state
        if state == PodWaitState.PROGRESSING and not should_print:
            should_print = now - self.last_progressing_print >= POD_POLL_INTERVAL_SECONDS

        if should_print:
            print(f"{self.label}: {state.value}")
            self.last_printed_state = state
            if state == PodWaitState.PROGRESSING:
                self.last_progressing_print = now


def print_pod_failure_hint(
    label: str,
    namespace: str,
    *,
    pod_name: Optional[str] = None,
    label_selector: Optional[str] = None,
) -> None:
    print(f"Warning: pod wait failed for {label}. Check pod status with:")
    if pod_name:
        print(f"  minikube kubectl -- get pod {pod_name} -n {shlex.quote(namespace)}")
        print(f"  minikube kubectl -- describe pod {pod_name} -n {shlex.quote(namespace)}")
    elif label_selector:
        print(f"  minikube kubectl -- get pods -n {shlex.quote(namespace)} -l {shlex.quote(label_selector)}")
        print(f"  minikube kubectl -- describe pod -n {shlex.quote(namespace)} " f"-l {shlex.quote(label_selector)}")
    else:
        print(f"  minikube kubectl -- get pods -n {shlex.quote(namespace)}")
        print(f"  minikube kubectl -- describe pod <pod-name> -n {shlex.quote(namespace)}")


def wait_for_pod(
    name: str,
    namespace: str,
    *,
    timeout_seconds: int = READY_TIMEOUT_SECONDS,
    expect_succeeded: bool = False,
    label: str = "",
) -> int:
    tracker = PodStateTracker(label or name)
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        pod = get_pod(name, namespace)
        state = classify_pod_state(
            pod,
            expect_succeeded=expect_succeeded,
            has_seen_running=tracker.has_seen_running,
        )
        tracker.observe(state)

        if state == PodWaitState.FINISHED:
            return 0
        if state == PodWaitState.FAILED:
            print_pod_failure_hint(label or name, namespace, pod_name=name)
            return 1

        time.sleep(POD_POLL_INTERVAL_SECONDS)

    tracker.observe(PodWaitState.FAILED)
    print(f"{label or name} did not reach FINISHED within {timeout_seconds}s.")
    print_pod_failure_hint(label or name, namespace, pod_name=name)
    return 1


def wait_for_labeled_pod(
    namespace: str,
    label_selector: str,
    *,
    display_name: str,
    timeout_seconds: int = READY_TIMEOUT_SECONDS,
    expect_succeeded: bool = False,
    annotation_key: Optional[str] = None,
    annotation_value: Optional[str] = None,
) -> int:
    tracker = PodStateTracker(display_name)
    deadline = time.time() + timeout_seconds
    watched_pod_name: Optional[str] = None

    while time.time() < deadline:
        pod_name = find_pod_name_by_label(
            namespace,
            label_selector,
            annotation_key=annotation_key,
            annotation_value=annotation_value,
        )
        if pod_name:
            watched_pod_name = pod_name

        pod = get_pod(watched_pod_name, namespace) if watched_pod_name else None
        state = classify_pod_state(
            pod,
            expect_succeeded=expect_succeeded,
            has_seen_running=tracker.has_seen_running,
        )
        tracker.observe(state)

        if state == PodWaitState.FINISHED:
            return 0
        if state == PodWaitState.FAILED:
            print_pod_failure_hint(
                display_name,
                namespace,
                pod_name=watched_pod_name,
                label_selector=label_selector,
            )
            return 1

        time.sleep(POD_POLL_INTERVAL_SECONDS)

    tracker.observe(PodWaitState.FAILED)
    print(f"{display_name} did not reach FINISHED within {timeout_seconds}s.")
    print_pod_failure_hint(
        display_name,
        namespace,
        pod_name=watched_pod_name,
        label_selector=label_selector,
    )
    return 1


def wait_for_deployment_rollout(
    application: str,
    namespace: str,
    pipeline_id: Optional[str],
    timeout_seconds: int = READY_TIMEOUT_SECONDS,
) -> int:
    label_selector = f"app.kubernetes.io/instance={application}"
    return wait_for_labeled_pod(
        namespace,
        label_selector,
        display_name=f"{application}-{namespace}",
        timeout_seconds=timeout_seconds,
        annotation_key="pipeline_id" if pipeline_id else None,
        annotation_value=pipeline_id,
    )


def wait_for_postgresql_ready(namespace: str, timeout_seconds: int = READY_TIMEOUT_SECONDS) -> int:
    return wait_for_pod(DEFAULT_POSTGRES_POD, namespace, timeout_seconds=timeout_seconds)


def wait_for_kafka_ready(namespace: str, timeout_seconds: int = READY_TIMEOUT_SECONDS) -> int:
    return wait_for_pod(DEFAULT_KAFKA_CONTROLLER_POD, namespace, timeout_seconds=timeout_seconds)


def wait_for_localstack_ready(namespace: str, timeout_seconds: int = READY_TIMEOUT_SECONDS) -> int:
    return wait_for_labeled_pod(
        namespace,
        f"app.kubernetes.io/instance={DEFAULT_LOCALSTACK_RELEASE}",
        display_name=DEFAULT_LOCALSTACK_RELEASE,
        timeout_seconds=timeout_seconds,
    )


def wait_for_kafka_ui_ready(namespace: str, timeout_seconds: int = READY_TIMEOUT_SECONDS) -> int:
    return wait_for_labeled_pod(
        namespace,
        f"app.kubernetes.io/instance={DEFAULT_KAFKA_UI_RELEASE}",
        display_name=DEFAULT_KAFKA_UI_RELEASE,
        timeout_seconds=timeout_seconds,
    )
