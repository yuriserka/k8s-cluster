from kafkaworker.core.models.example_event.payloads.kafka_message import (
    EventTypes,
    ExampleTopicEventDTO,
)
from kafkaworker.core.factories.example_topic.dtos import (
    SendMessageToUserEventPayloadDTO,
    SendWeatherReportEventPayloadDTO,
)


class ExampleTopicPayloadFactory:
    def __init__(self):
        self.event_types = {
            EventTypes.SEND_MESSAGE_TO_USER: SendMessageToUserEventPayloadDTO,
            EventTypes.SEND_WEATHER_REPORT: SendWeatherReportEventPayloadDTO,
        }

    def parse_message_to_dto(self, message: dict) -> ExampleTopicEventDTO:
        event_type = message.pop("event_type", None)
        if not event_type:
            raise ValueError("Event type is required in the message")

        event_type = EventTypes(event_type)
        if event_type not in self.event_types:
            raise ValueError(f"Unknown event type: {event_type}")

        payload = message.pop("payload", {})

        return ExampleTopicEventDTO(
            **message,
            event_type=event_type,
            payload=self.event_types[event_type](**payload),
        )
