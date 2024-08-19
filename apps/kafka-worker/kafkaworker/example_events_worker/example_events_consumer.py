import logging
from typing import Optional
from kafkaworker.config import config

from kafkaworker.core.models.example_event.payloads.kafka_message import (
    ExampleEventPayloadDTO,
    ExampleEventDataDTO
)
from kafkaworker.core.services.example_events_service import (
    ExampleEventsService
)
from kafkaworker.core.kafka.consumer.abstract_kafka_consumer import (
    AbstractKafkaConsumer
)

logger = logging .getLogger(__name__)
kafka_config = config["KAFKA"]


class ExampleEventKafkaConsumer(AbstractKafkaConsumer[ExampleEventPayloadDTO]):
    def __init__(self, example_events_service: ExampleEventsService):
        super().__init__(topic=kafka_config.get("TOPICS").get("EXAMPLE_EVENTS"))
        self.example_events_service = example_events_service

    async def parse_message(self, message: dict) -> ExampleEventPayloadDTO:
        data = message.pop("data", {})
        return ExampleEventPayloadDTO(
            **message,
            data=ExampleEventDataDTO(**data),
        )

    async def handle_message(self, key: Optional[str], message: ExampleEventPayloadDTO):
        logger.info(
            f"saving message {message.id} from user {message.data.name}"
        )
        await self.example_events_service.save_event(message)
