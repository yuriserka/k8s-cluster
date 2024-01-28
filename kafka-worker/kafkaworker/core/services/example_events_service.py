import logging

from kafkaworker.core.models.example_event.example_event_model import ExampleEventModel
from kafkaworker.core.models.example_event.payloads.kafka_message import ExampleEventPayloadDTO

logger = logging.getLogger(__name__)


class ExampleEventsService():
    def save_event(self, event: ExampleEventPayloadDTO):
        saved_event = ExampleEventModel.objects.create(
            event_id=event.id,
            event_type=event.type,
            user_id=event.data.user_id,
            username=event.data.name,
        )

        logger.info(f"saved event: {saved_event}")
