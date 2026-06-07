from enum import Enum
from typing import NamedTuple, Optional


class InstallMode(str, Enum):
    cluster = "cluster"
    compose = "compose"


class DropMode(str, Enum):
    cluster = "cluster"
    compose = "compose"


class InfraService(str, Enum):
    postgresql = "postgresql"
    kafka = "kafka"
    localstack = "localstack"
    kafka_ui = "kafka-ui"


class InstallInfraRequest(NamedTuple):
    mode: InstallMode
    namespace: str
    with_kafka_ui: bool


class DropInfraRequest(NamedTuple):
    mode: DropMode
    namespace: str
    services: Optional[list[InfraService]]
    remove_volumes: bool
