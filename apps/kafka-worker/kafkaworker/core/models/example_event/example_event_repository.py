from kafkaworker.core.models.example_event_model import ExampleEventModel
from concurrency.exceptions import RecordModifiedError
import logging

logger = logging.getLogger(__name__)


class ExampleEventRepository:
    async def create_event(self, event: ExampleEventModel) -> ExampleEventModel:
        return await ExampleEventModel.objects.acreate(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload,
        )

    async def get_event(self, event_id: str) -> ExampleEventModel:
        return await ExampleEventModel.objects.aget(event_id=event_id)

    async def update_event_payload(self, event: ExampleEventModel, new_attributes: dict) -> ExampleEventModel:
        event.payload = {
            **event.payload,
            **new_attributes,
        }
        try:
            return await event.asave()
        except RecordModifiedError as e:
            logger.error(f"record modified error updating event payload: {e}", exc_info=True)
            raise e
        except Exception as e:
            logger.error(f"error updating event payload: {e}", exc_info=True)
            raise
