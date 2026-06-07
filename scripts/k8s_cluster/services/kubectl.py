import json
import shlex
import subprocess
from typing import Optional

from k8s_cluster.utils.shell import execute_cli_command


def run_kubectl_json(args: list) -> Optional[dict]:
    result = subprocess.run(
        ["minikube", "kubectl", "--", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def list_pods(namespace: str, label_selector: Optional[str] = None) -> list:
    args = ["get", "pods", "-n", namespace, "-o", "json"]
    if label_selector:
        args.extend(["-l", label_selector])
    data = run_kubectl_json(args)
    if not data:
        return []
    return data.get("items", [])


def get_pod(name: str, namespace: str) -> Optional[dict]:
    return run_kubectl_json(["get", "pod", name, "-n", namespace, "-o", "json"])


def delete_pod(name: str, namespace: str) -> None:
    execute_cli_command(
        f"minikube kubectl -- delete pod {shlex.quote(name)} -n {shlex.quote(namespace)} " "--ignore-not-found=true"
    )


def pod_has_ready_condition(pod: dict) -> bool:
    for condition in pod.get("status", {}).get("conditions", []):
        if condition.get("type") == "Ready" and condition.get("status") == "True":
            return True
    return False


def container_statuses(pod: dict) -> list:
    return pod.get("status", {}).get("containerStatuses") or []


def is_container_creating(pod: dict) -> bool:
    init_statuses = pod.get("status", {}).get("initContainerStatuses") or []
    for status in init_statuses + container_statuses(pod):
        waiting = status.get("state", {}).get("waiting", {})
        reason = waiting.get("reason", "")
        if reason in ("ContainerCreating", "PodInitializing"):
            return True
    return False


def has_running_container(pod: dict) -> bool:
    return any(status.get("state", {}).get("running") for status in container_statuses(pod))


def all_containers_ready(pod: dict) -> bool:
    statuses = container_statuses(pod)
    return bool(statuses) and all(status.get("ready") for status in statuses)


def get_failed_exit_code(pod: dict) -> Optional[int]:
    phase = pod.get("status", {}).get("phase")
    if phase == "Failed":
        return 1

    for status in container_statuses(pod):
        terminated = status.get("state", {}).get("terminated")
        if terminated and terminated.get("exitCode", 0) != 0:
            return terminated.get("exitCode", 1)
    return None


def get_pod_container_exit_code(pod: dict, container_name: Optional[str] = None) -> int:
    for status in container_statuses(pod):
        if container_name and status.get("name") != container_name:
            continue
        terminated = status.get("state", {}).get("terminated")
        if terminated is not None:
            return terminated.get("exitCode", 1)
    return 0


def find_pod_name_by_label(
    namespace: str,
    label_selector: str,
    *,
    annotation_key: Optional[str] = None,
    annotation_value: Optional[str] = None,
) -> Optional[str]:
    pods = list_pods(namespace, label_selector)
    if annotation_key is not None:
        pods = [
            pod
            for pod in pods
            if pod.get("metadata", {}).get("annotations", {}).get(annotation_key) == annotation_value
        ]

    if not pods:
        return None

    pods.sort(key=lambda pod: pod.get("metadata", {}).get("creationTimestamp", ""), reverse=True)
    return pods[0]["metadata"]["name"]
