import random
from kafkaworker.containers.scheduler.jobs.schedule_job import ScheduleJob, ScheduleJobType
import logging

from kafkaworker.core.models.example_event_model import ExampleEventModel
from kafkaworker.core.services.example_events_service import ExampleEventsService

logger = logging.getLogger(__name__)


class UpdateEventJob(ScheduleJob):
    def __init__(self, example_events_service: ExampleEventsService):
        self.example_events_service = example_events_service
        super().__init__(
            name="update_event_job",
            type=ScheduleJobType.INTERVAL,
            interval_seconds=10,
        )

    async def execute(self) -> None:
        try:
            await self.update_events()
        except Exception as e:
            logger.error(f"error updating events in the database: {e}", exc_info=True)
            raise

    async def update_events(self):
        all_events = [e async for e in ExampleEventModel.objects.all()]
        logger.info("found %s events in the database", len(all_events))
        if len(all_events) == 0:
            logger.info("no events found in the database")
            return

        random_events = self.__get_list_of_random_events(all_events)
        for random_event in random_events:
            random_number = random.uniform(1.0, 5000.0)
            logger.info(f"Updating event {random_event.event_id} with random number {random_number}")
            await self.example_events_service.update_event_payload(
                event_id=random_event.event_id,
                new_attributes={
                    "random_number": random_number,
                },
            )
            logger.info(f"Event {random_event.event_id} updated successfully with random number {random_number}")

    def __get_list_of_random_events(self, all_events: list[ExampleEventModel]) -> list[ExampleEventModel]:
        return random.sample(all_events, random.randint(1, len(all_events)))
