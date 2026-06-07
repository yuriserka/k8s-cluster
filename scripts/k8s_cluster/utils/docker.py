import os


def is_minikube_docker_env() -> bool:
    if os.environ.get("MINIKUBE_ACTIVE_DOCKERD"):
        return True
    docker_host = os.environ.get("DOCKER_HOST", "")
    cert_path = os.environ.get("DOCKER_CERT_PATH", "")
    return docker_host.startswith("tcp://") and "minikube" in cert_path


def docker_desktop_env_prefix() -> str:
    return (
        "unset DOCKER_TLS_VERIFY DOCKER_CERT_PATH MINIKUBE_ACTIVE_DOCKERD; " "DOCKER_HOST=unix:///var/run/docker.sock "
    )
