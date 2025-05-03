import logging

from kafkaworker.core.models import ExampleEventModel
from kafkaworker.core.models.example_event.payloads.kafka_message import ExampleTopicEventDTO
from kafkaworker.core.factories.example_topic.payload_factory import SendMessageToUserEventPayloadDTO

logger = logging.getLogger(__name__)


class ExampleEventsService:
    async def save_event(self, event: ExampleTopicEventDTO[SendMessageToUserEventPayloadDTO]):
        saved_event = await ExampleEventModel.objects.acreate(
            event_id=event.event_id,
            event_type=event.event_type,
            user_id=event.payload.user_id,
            username=event.payload.name,
        )

        logger.info(f"saved event: {saved_event}")
