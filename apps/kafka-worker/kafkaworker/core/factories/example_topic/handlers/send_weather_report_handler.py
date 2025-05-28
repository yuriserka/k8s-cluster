import logging
from typing import Optional

from kafkaworker.core.factories.example_topic.payload_factory import (
    SendWeatherReportEventPayloadDTO
)

from kafkaworker.core.kafka.consumer.abstract_kafka_event_handler import (
    AbstractKafkaEventHandler,
)
from kafkaworker.core.models.example_event.payloads.kafka_message import ExampleTopicEventDTO

logger = logging.getLogger(__name__)


class SendWeatherReportHandler(
    AbstractKafkaEventHandler[str, ExampleTopicEventDTO[SendWeatherReportEventPayloadDTO]]
):
    def __init__(self):
        super().__init__()

    async def handle(
            self,
            key: Optional[str],
            event: ExampleTopicEventDTO[SendWeatherReportEventPayloadDTO]
    ):
        logger.info(f"Received weather report: {event}")
        temperature = float(event.payload.temperature.split(" ")[0])

        if temperature <= 0:
            logger.error(f"Temperature is below freezing in {event.payload.address}: {temperature}°C")
            raise ValueError(
                f"unacceptable temperature of {temperature}°C for report {event.payload.report_id}"
            )

        if temperature <= 20:
            logger.warning(
                f"Low temperature alert in {event.payload.address}: {temperature}°C"
            )
        elif temperature >= 30:
            logger.warning(
                f"High temperature alert in {event.payload.address}: {temperature}°C"
            )
        else:
            logger.info(
                f"Normal temperature for report: {temperature}°C"
            )

        logger.info(f"report {event.payload.report_id} processed successfully")
