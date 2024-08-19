import json
import logging
from typing import Generic, Optional, TypeVar
from kafka import KafkaConsumer
from kafkaworker.config import config

from abc import ABC, abstractmethod
logger = logging .getLogger(__name__)
kafka_config = config["KAFKA"]

T = TypeVar("T")


class AbstractKafkaConsumer(ABC, Generic[T]):
    def __init__(self, topic: str):
        self.topic = topic
        self.consumer = KafkaConsumer(
            bootstrap_servers=kafka_config.get("KAFKA_BOOTSTRAP_SERVERS"),
            group_id=kafka_config.get("KAFKA_CONSUMER_GROUP_ID"),
            auto_offset_reset='latest',
            value_deserializer=lambda msg: json.loads(msg.decode("utf-8")),
        )
        logger.info(f"Consumer created for topic {self.topic}")

    async def run(self):
        self.consumer.subscribe([self.topic])
        try:
            while True:
                await self._consume_messages()
        except Exception as e:
            logger.error(
                f"Error while polling messages from topic {self.topic} {e}",
                exc_info=True,
                extra={"topic": self.topic}
            )
        finally:
            logger.warning(f"Closing consumer for topic {self.topic}")
            self.consumer.close()

    async def _consume_messages(self):
        pulled_messages = self.consumer.poll(max_records=5, timeout_ms=5000)
        if not pulled_messages:
            return
        for topic_partition, messages in pulled_messages.items():
            for message in messages:
                await self._base_handle_message(message, topic_partition)

    async def _base_handle_message(self, message, topic_partition):
        topic = topic_partition.topic
        partition = topic_partition.partition

        try:
            parsed_message = await self.parse_message(message.value)
        except Exception as e:
            logger.error(
                f"Error while parsing message from topic {topic}:{partition} {e}",
                exc_info=True,
                extra={"message": message.value, "topic": topic}
            )
            return

        try:
            logger.info(
                f"Consuming message from topic {topic}:{partition} with key {message.key}: {parsed_message}"
            )
            await self.handle_message(message.key, parsed_message)
        except Exception as e:
            logger.error(
                f"Error while consuming message from topic {topic}:{partition} {e}",
                exc_info=True,
                extra={"message": message, "topic": topic}
            )

    @abstractmethod
    def handle_message(self, key: Optional[str], message: T):
        raise NotImplementedError()

    @abstractmethod
    def parse_message(self, message: dict) -> T:
        raise NotImplementedError()
