import atexit
import os

from testcontainers.postgres import PostgresContainer

POSTGRES_IMAGE = 'postgres:16.3'

_container: PostgresContainer | None = None


def _is_minikube_docker_env() -> bool:
    if os.environ.get('MINIKUBE_ACTIVE_DOCKERD'):
        return True
    docker_host = os.environ.get('DOCKER_HOST', '')
    cert_path = os.environ.get('DOCKER_CERT_PATH', '')
    return docker_host.startswith('tcp://') and 'minikube' in cert_path


def _use_docker_desktop_for_testcontainers() -> None:
    if not _is_minikube_docker_env():
        return
    print('Using Docker Desktop for tests (minikube docker-env detected)')
    for key in ('DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH', 'MINIKUBE_ACTIVE_DOCKERD'):
        os.environ.pop(key, None)
    os.environ['DOCKER_HOST'] = 'unix:///var/run/docker.sock'


def start_postgres_container() -> PostgresContainer:
    global _container
    if _container is not None:
        return _container

    _use_docker_desktop_for_testcontainers()
    _container = PostgresContainer(POSTGRES_IMAGE)
    _container.start()
    atexit.register(stop_postgres_container)

    os.environ['DATABASE_HOST'] = _container.get_container_host_ip()
    os.environ['DATABASE_PORT'] = str(_container.get_exposed_port(5432))
    os.environ['DATABASE_USER'] = _container.username
    os.environ['DATABASE_PASSWORD'] = _container.password
    os.environ['DATABASE_NAME'] = _container.dbname

    return _container


def stop_postgres_container() -> None:
    global _container
    if _container is not None:
        _container.stop()
        _container = None


def get_database_config() -> dict:
    container = start_postgres_container()
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': container.dbname,
        'USER': container.username,
        'PASSWORD': container.password,
        'HOST': container.get_container_host_ip(),
        'PORT': container.get_exposed_port(5432),
    }
