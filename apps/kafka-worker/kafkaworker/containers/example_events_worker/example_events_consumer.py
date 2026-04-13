import logging
from typing import Optional
from kafkaworker.config import config

from kafkaworker.core.models.example_event.payloads.kafka_message import (
    ExampleTopicEventDTO,
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
        try:
            await self.handler_factory.handle_event(key, message)
        except Exception as e:
            logger.error(
                f"Error while handling message with key {key}: {e}",
                exc_info=True,
                extra={"event_message": message, "key": key}
            )
            raise e
