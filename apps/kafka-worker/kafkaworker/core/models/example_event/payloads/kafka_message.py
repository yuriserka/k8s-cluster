from typing import NamedTuple


class ExampleEventDataDTO(NamedTuple):
    user_id: str
    name: str


class ExampleEventPayloadDTO(NamedTuple):
    id: str
    type: str
    timestamp: str
    data: ExampleEventDataDTO
