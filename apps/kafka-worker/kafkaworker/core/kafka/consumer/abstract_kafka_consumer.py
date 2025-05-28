from asyncio import sleep, gather
import json
import logging
from typing import Generic, NamedTuple, Optional, TypeVar
from kafka import KafkaConsumer, TopicPartition
from kafkaworker.config import config
from kafkaworker.core.utils.exponential_backoff import get_expo_backoff


from abc import ABC, abstractmethod
logger = logging .getLogger(__name__)

T = TypeVar("T")


class RetryableMessage(NamedTuple, Generic[T]):
    key: str
    message: T
    offset: int
    retry_count: int = 0


class RetryBuffer(NamedTuple, Generic[T]):
    topic_partition: TopicPartition
    messages: list[RetryableMessage[T]]


class AbstractKafkaConsumer(ABC, Generic[T]):
    MAX_MESSAGE_RETRIES = 3
    BASE_RETRY_DELAY_SECONDS = 5

    def __init__(self, topic: str):
        self.topic = topic
        self.consumer = KafkaConsumer(
            bootstrap_servers=config.get("KAFKA_BOOTSTRAP_SERVERS"),
            group_id=config.get("KAFKA_CONSUMER_GROUP_ID"),
            value_deserializer=lambda msg: json.loads(msg.decode("utf-8")),
            enable_auto_commit=False,
        )
        self.buffer: RetryBuffer[T] = {}
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
        for topic_partition, messages in self.buffer.items():
            await gather(
                *[self._retry_message(message, topic_partition) for message in messages]
            )
        pulled_messages = self.consumer.poll(max_records=5, timeout_ms=5000)
        for topic_partition, messages in pulled_messages.items():
            await gather(
                *[self._base_handle_message(message, topic_partition) for message in messages]
            )

    async def _retry_message(self, retry_message: RetryableMessage[T], topic_partition: TopicPartition):
        parsed_message = retry_message.message
        self.buffer.get(topic_partition, []).remove(retry_message)

        if retry_message.retry_count >= self.MAX_MESSAGE_RETRIES:
            topic = topic_partition.topic
            partition = topic_partition.partition
            logger.error(
                f"Max retries reached for message from topic {topic}:{partition}: {parsed_message}",
                extra={"event_message": parsed_message, "topic": topic}
            )
            self.consumer.commit()
            return

        try:
            await sleep(
                get_expo_backoff(
                    attempt_number=retry_message.retry_count,
                    base_delay=self.BASE_RETRY_DELAY_SECONDS,
                    max_delay=20,
                    jitter=True
                )
            )
            await self.handle_message(retry_message.key, parsed_message)
            self.consumer.commit()
        except Exception:
            self.buffer = {
                **self.buffer,
                topic_partition: [
                    *self.buffer.get(topic_partition, []),
                    RetryableMessage(
                        key=retry_message.key,
                        message=parsed_message,
                        offset=retry_message.offset,
                        retry_count=retry_message.retry_count + 1,
                    )
                ]
            }

    async def _base_handle_message(self, message, topic_partition: TopicPartition):
        topic = topic_partition.topic
        partition = topic_partition.partition

        logger.info(
            f"incoming message in topic {topic}:{partition} with key {message.key}: {message}"
        )
        parsed_message = await self._parse_message(message, topic, partition)
        if not parsed_message:
            return

        try:
            logger.info(
                f"Consuming message from topic {topic}:{partition} with key {message.key}: {parsed_message}"
            )
            await self.handle_message(message.key, parsed_message)
            self.consumer.commit()
        except Exception as e:
            logger.error(
                f"Error while consuming message from topic {topic}:{partition} {e}",
                exc_info=True,
                extra={"event_message": parsed_message, "topic": topic}
            )
            self.buffer = {
                **self.buffer,
                topic_partition: [
                    *self.buffer.get(topic_partition, []),
                    RetryableMessage(
                        key=message.key,
                        message=parsed_message,
                        offset=message.offset,
                        retry_count=0
                    )
                ]
            }

    async def _parse_message(self, message, topic: str, partition: int) -> Optional[T]:
        try:
            return await self.parse_message(message.value)
        except Exception as e:
            logger.error(
                f"Error while parsing message from topic {topic}:{partition} {e}",
                exc_info=True,
                extra={"raw_event_value": message.value, "topic": topic}
            )

    @abstractmethod
    async def handle_message(self, key: Optional[str], message: T):
        raise NotImplementedError()

    @abstractmethod
    async def parse_message(self, message: dict) -> T:
        raise NotImplementedError()
