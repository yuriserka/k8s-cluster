import os
import shlex

DEFAULT_POSTGRES_SERVICE = "postgresql"
DEFAULT_KAFKA_CONTROLLER_POD = "kafka-controller-0"
DEFAULT_LOCALSTACK_RELEASE = "localstack"
READY_TIMEOUT_SECONDS = 120


def execute_cli_command(command: str) -> int:
    print(f"Executing command: {command}")
    return os.system(command)


def wait_for_postgresql_ready(namespace: str, timeout_seconds: int = READY_TIMEOUT_SECONDS) -> int:
    return execute_cli_command(
        "minikube kubectl -- wait --for=condition=ready "
        f"pod/{DEFAULT_POSTGRES_SERVICE}-0 -n {shlex.quote(namespace)} "
        f"--timeout={timeout_seconds}s"
    )


def wait_for_kafka_ready(namespace: str, timeout_seconds: int = READY_TIMEOUT_SECONDS) -> int:
    return execute_cli_command(
        "minikube kubectl -- wait --for=condition=ready "
        f"pod/{DEFAULT_KAFKA_CONTROLLER_POD} -n {shlex.quote(namespace)} "
        f"--timeout={timeout_seconds}s"
    )


def wait_for_localstack_ready(namespace: str, timeout_seconds: int = READY_TIMEOUT_SECONDS) -> int:
    return execute_cli_command(
        "minikube kubectl -- wait --for=condition=available "
        f"deployment/{DEFAULT_LOCALSTACK_RELEASE} -n {shlex.quote(namespace)} "
        f"--timeout={timeout_seconds}s"
    )
