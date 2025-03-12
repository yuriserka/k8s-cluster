import logging

from kafkaworker.core.models import ExampleEventModel
from kafkaworker.core.models.example_event.payloads.kafka_message import ExampleEventPayloadDTO

logger = logging.getLogger(__name__)


class ExampleEventsService():
    async def save_event(self, event: ExampleEventPayloadDTO):
        saved_event = await ExampleEventModel.objects.acreate(
            event_id=event.id,
            event_type=event.type,
            user_id=event.data.user_id,
            username=event.data.name,
        )

        logger.info(f"saved event: {saved_event}")
