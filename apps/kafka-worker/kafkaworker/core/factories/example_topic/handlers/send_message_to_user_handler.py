import logging
from random import randint
from typing import Optional

from kafkaworker.core.factories.example_topic.payload_factory import (
    SendMessageToUserEventPayloadDTO,
)

from kafkaworker.core.kafka.consumer.abstract_kafka_event_handler import (
    AbstractKafkaEventHandler,
)
from kafkaworker.core.models.example_event.payloads.kafka_message import (
    ExampleTopicEventDTO,
)

logger = logging.getLogger(__name__)


class SendMessageToUserHandler(
    AbstractKafkaEventHandler[str, SendMessageToUserEventPayloadDTO]
):
    def __init__(self, example_events_service):
        super().__init__()
        self.example_events_service = example_events_service

    async def handle(
        self, key: Optional[str], event: ExampleTopicEventDTO[SendMessageToUserEventPayloadDTO]
    ):
        if event.username == "error":
            raise Exception(f"error event {event.id} received")

        if event.username == "test":
            logger.info(f"event {event.id} is a test event")

            rand_id_index = randint(0, len(event.id) - 1)
            checked_char = event.id[rand_id_index]
            if ord(checked_char) % 2 == 0:
                raise Exception(
                    f"test event {event.id} failed due to character {checked_char} at index {rand_id_index}"
                )
            else:
                logger.info(f"test event {event.id} passed")

        logger.info(f"saving event {event.id} from user {event.username}")
        await self.example_events_service.save_event(event)
