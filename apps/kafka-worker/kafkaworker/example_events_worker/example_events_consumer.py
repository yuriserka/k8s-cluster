from random import randint
import logging
from typing import Optional
from kafkaworker.config import config

from kafkaworker.core.models.example_event.payloads.kafka_message import (
    ExampleTopicEventDTO,
    ExampleEventDataDTO
)
from kafkaworker.core.services.example_events_service import (
    ExampleEventsService
)
from kafkaworker.core.kafka.consumer.abstract_kafka_consumer import (
    AbstractKafkaConsumer
)
from kafkaworker.core.factories.example_topic import (
    ExampleTopicHandlerFactory,
    ExampleTopicPayloadFactory
)

logger = logging .getLogger(__name__)


class ExampleEventKafkaConsumer(AbstractKafkaConsumer[ExampleTopicEventDTO]):
    def __init__(self):
        super().__init__(topic=config.get("KAFKA_TOPICS_EXAMPLE_EVENTS"))
        self.payload_factory = ExampleTopicPayloadFactory()
        self.handler_factory = ExampleTopicHandlerFactory()

    async def parse_message(self, message: dict):
        return self.payload_factory.parse_message_to_dto(message)

    async def handle_message(self, key: Optional[str], message: ExampleTopicEventDTO):
        self.handler_factory.handle_event(key, message)
