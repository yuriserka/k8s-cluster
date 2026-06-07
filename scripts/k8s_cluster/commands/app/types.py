from typing import NamedTuple, Optional


class DropAppRequest(NamedTuple):
    repository: str
    namespace: str


class PublishAppRequest(NamedTuple):
    repository: str
    dockerfile: str
    app_path: str
    namespace: str
    tag: Optional[str]
    use_minikube_docker: bool
    build_args: Optional[dict]


class InstallAppRequest(NamedTuple):
    application: str
    repository: str
    params_file: str
    app_path: str
    namespace: str
    tag: Optional[str]
    pipeline_id: Optional[str]
    pipeline_started_at: Optional[str]
