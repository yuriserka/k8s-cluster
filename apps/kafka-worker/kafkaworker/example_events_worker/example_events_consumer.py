from random import randint
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


class ExampleEventKafkaConsumer(AbstractKafkaConsumer[ExampleEventPayloadDTO]):
    def __init__(self, example_events_service: ExampleEventsService):
        super().__init__(topic=config.get("KAFKA_TOPICS_EXAMPLE_EVENTS"))
        self.example_events_service = example_events_service

    async def parse_message(self, message: dict) -> ExampleEventPayloadDTO:
        data = message.pop("data", {})
        return ExampleEventPayloadDTO(
            **message,
            data=ExampleEventDataDTO(**data),
        )

    async def handle_message(self, key: Optional[str], message: ExampleEventPayloadDTO):
        if message.data.name == "error":
            logger.error(
                f"message {message.id} is an error message"
            )
            raise Exception(
                f"error message {message.id} received"
            )

        if message.data.name == "test":
            logger.info(
                f"message {message.id} is a test message"
            )

            rand_id_index = randint(0, len(message.id) - 1)
            checked_char = message.id[rand_id_index]
            if ord(checked_char) % 2 == 0:
                raise Exception(
                    f"test message {message.id} failed due to character {checked_char} at index {rand_id_index}"
                )
            else:
                logger.info(f"test message {message.id} passed")

        logger.info(
            f"saving message {message.id} from user {message.data.name}"
        )
        await self.example_events_service.save_event(message)
