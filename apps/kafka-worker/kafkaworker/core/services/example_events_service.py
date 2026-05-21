import logging

from kafkaworker.core.models import ExampleEventModel
from kafkaworker.core.models.example_event.example_event_repository import ExampleEventRepository
from kafkaworker.core.models.example_event.payloads.kafka_message import ExampleTopicEventDTO

logger = logging.getLogger(__name__)


class ExampleEventsService:
    def __init__(self, example_event_repository: ExampleEventRepository):
        self.example_event_repository = example_event_repository

    async def save_event(self, event: ExampleTopicEventDTO):
        saved_event = await self.example_event_repository.create_event(
            ExampleEventModel(
                event_id=event.event_id,
                event_type=event.event_type.value,
                payload=event.payload,
            )
        )
        logger.info(f"saved event: {saved_event}")
        return saved_event

    async def update_event_payload(self, event_id: str, new_attributes: dict):
        event = await self.example_event_repository.get_event(event_id)
        logger.info(f"previous event payload: {event.payload}")
        if not event:
            raise ValueError(f"Event with id {event_id} not found")

        updated_event = await self.example_event_repository.update_event_payload(event, new_attributes)
        logger.info(f"updated event payload: {updated_event.payload}")
        return updated_event