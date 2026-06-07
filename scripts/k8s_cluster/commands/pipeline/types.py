from typing import NamedTuple


class ServiceArgs(NamedTuple):
    image: str
    image_env_vars: dict
    image_port_map: str
    env_vars: dict
    output_file: str


class DatabaseMigrationStepArgs(NamedTuple):
    kind: str
    env: str
    repository: str
    image_repo: str
    cmd: list[str]


class CredentialsStepArgs(NamedTuple):
    kind: str
    path: str
    output_file: str


class InstallStepArgs(NamedTuple):
    kind: str
    application: str
    params_file: str
    repo: str
    env: str


class PublishStepArgs(NamedTuple):
    kind: str
    repo: str
    env: str
    dockerfile: str
    build_args: dict = {}


class PipelineContext(NamedTuple):
    repository: str
    temp_folder: str
    pipeline_id: str
    pipeline_started_at: str
