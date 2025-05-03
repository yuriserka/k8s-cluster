from typing import Optional

from kafkaworker.core.factories.example_topic.handlers import (
    SendMessageToUserHandler,
    SendWeatherReportHandler,
)
from kafkaworker.core.models.example_event.payloads.kafka_message import (
    EventTypes,
    ExampleTopicEventDTO,
)
from kafkaworker.core.services.example_events_service import ExampleEventsService

send_message_to_user_handler = SendMessageToUserHandler(
    example_events_service=ExampleEventsService()
)
send_weather_report_handler = SendWeatherReportHandler()


class ExampleTopicHandlerFactory:
    def __init__(self):
        self.event_types = {
            EventTypes.SEND_MESSAGE_TO_USER: send_message_to_user_handler,
            EventTypes.SEND_WEATHER_REPORT: send_weather_report_handler,
        }

    def handle_event(self, key: Optional[str], event: ExampleTopicEventDTO):
        self.event_types[event.event_type].handle(key, event)
