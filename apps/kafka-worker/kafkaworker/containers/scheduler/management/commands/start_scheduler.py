import asyncio
import logging
from django.core.management.base import BaseCommand

from kafkaworker.containers.scheduler.jobs.update_event_job import UpdateEventJob
from kafkaworker.containers.scheduler.scheduler import Scheduler
from kafkaworker.core.models.example_event.example_event_repository import ExampleEventRepository
from kafkaworker.core.services.example_events_service import ExampleEventsService

logger = logging.getLogger(__name__)


example_events_service = ExampleEventsService(example_event_repository=ExampleEventRepository())


class Command(BaseCommand):
    help = "start kafka-worker-scheduler"

    def handle(self, *args, **options):
        logger.info("starting kafka-worker-scheduler")
        asyncio.run(self.__run_scheduler())

    async def __run_scheduler(self) -> None:
        scheduler = Scheduler(
            [
                UpdateEventJob(example_events_service=example_events_service),
            ]
        )
        scheduler.start()
        await asyncio.Event().wait()
