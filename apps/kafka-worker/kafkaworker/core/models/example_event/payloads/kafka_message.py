from enum import Enum
from typing import NamedTuple, TypeVar, Generic

T = TypeVar("T")


class EventTypes(Enum):
    SEND_MESSAGE_TO_USER = "SEND_MESSAGE_TO_USER"
    SEND_WEATHER_REPORT = "SEND_WEATHER_REPORT"


class ExampleTopicEventDTO(NamedTuple, Generic[T]):
    id: int
    event_id: str
    event_type: EventTypes
    created_at: str
    payload: T
