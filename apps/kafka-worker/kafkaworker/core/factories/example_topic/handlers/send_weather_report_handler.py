import logging
from typing import Optional

from kafkaworker.core.factories.example_topic.payload_factory import (
    SendWeatherReportEventPayloadDTO
)

from kafkaworker.core.kafka.consumer.abstract_kafka_event_handler import (
    AbstractKafkaEventHandler,
)

logger = logging.getLogger(__name__)


class SendWeatherReportHandler(AbstractKafkaEventHandler[str, SendWeatherReportEventPayloadDTO]):
    async def handle(self, key: Optional[str], event: SendWeatherReportEventPayloadDTO):
        logger.info(f"Received weather report: {event}")
