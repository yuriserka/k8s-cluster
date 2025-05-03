from typing import TypeVar, NamedTuple

from kafkaworker.core.models.example_event.payloads.kafka_message import (
    EventTypes,
    ExampleTopicEventDTO,
)

T = TypeVar("T")


class SendMessageToUserEventPayloadDTO(NamedTuple):
    user_id: str
    username: str


class SendWeatherReportEventPayloadDTO(NamedTuple):
    reportId: str
    address: str
    temperature: str
    windSpeed: str
    windDirection: str
    timestamp: str


class ExampleTopicPayloadFactory:
    def __init__(self):
        self.event_types = {
            EventTypes.SEND_MESSAGE_TO_USER: SendMessageToUserEventPayloadDTO,
            EventTypes.SEND_WEATHER_REPORT: SendWeatherReportEventPayloadDTO,
        }

    def parse_message_to_dto(self, message: dict) -> ExampleTopicEventDTO[T]:
        event_type = message.pop("event_type", None)
        if event_type not in self.event_types:
            raise ValueError(f"Unknown event type: {event_type}")

        payload = message.pop("payload", {})

        return ExampleTopicEventDTO(
            **message,
            event_type=event_type,
            payload=self.event_types[event_type](**payload),
        )
