import yaml

from k8s_cluster.commands.pipeline.types import (
    CredentialsStepArgs,
    DatabaseMigrationStepArgs,
    InstallStepArgs,
    PublishStepArgs,
    ServiceArgs,
)


def load_pipeline_file(file_path: str) -> dict:
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def parse_service_args(service_args: dict) -> ServiceArgs:
    return ServiceArgs(**service_args)


def parse_step_args(kind: str, step_args: dict):
    if kind == "database_migration":
        return DatabaseMigrationStepArgs(**step_args)
    if kind == "credentials":
        return CredentialsStepArgs(**step_args)
    if kind == "install":
        return InstallStepArgs(**step_args)
    if kind == "publish":
        return PublishStepArgs(**step_args)
    return None
