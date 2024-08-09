import json
import logging
from typing import Optional
from kafka import KafkaConsumer
from kafkaworker.config import config

from kafkaworker.core.models.example_event.payloads.kafka_message import (
    ExampleEventPayloadDTO,
    ExampleEventDataDTO
)
from kafkaworker.core.services.example_events_service import (
    ExampleEventsService
)

logger = logging .getLogger(__name__)
kafka_config = config["KAFKA"]


class ExampleEventConsumer():
    def __init__(self, example_events_service: ExampleEventsService):
        self.example_events_service = example_events_service
        self.consumer = KafkaConsumer(
            kafka_config.get("TOPICS").get("EXAMPLE_EVENTS"),
            bootstrap_servers=kafka_config.get("KAFKA_BOOTSTRAP_SERVERS"),
            group_id=kafka_config.get("KAFKA_CONSUMER_GROUP_ID"),
            auto_offset_reset='earliest',
            value_deserializer=lambda msg: json.loads(msg.decode("utf-8")),
        )

    def run(self):
        try:
            while True:
                pulled_messages = self.consumer.poll(
                    max_records=5,
                    timeout_ms=5000
                )
                if pulled_messages:
                    for topic_partition, messages in pulled_messages.items():
                        logger.info(
                            f"Received {len(messages)} messages in "
                            f"topic {topic_partition.topic}:{topic_partition.partition}"
                        )
                        for message in messages:
                            self.handle_message(message.key, message.value)
        except Exception as e:
            logger.error(f"Error while consuming message: {e}")
            self.consumer.close()

    def handle_message(self, key: Optional[str], message: Optional[dict]):
        logger.info(f"Consuming message with key {key}: {message}")
        parsed_payload = ExampleEventPayloadDTO(
            id=message["id"],
            type=message["type"],
            timestamp=message["timestamp"],
            data=ExampleEventDataDTO(
                user_id=message["data"]["user_id"],
                name=message["data"]["name"],
            ),
        )
        logger.info(f"event payload: {parsed_payload}")

        self.example_events_service.save_event(parsed_payload)
