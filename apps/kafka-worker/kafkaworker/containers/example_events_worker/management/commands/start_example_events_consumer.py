import asyncio
import logging

from django.core.management.base import BaseCommand

from kafkaworker.containers.example_events_worker.example_events_consumer import ExampleEventKafkaConsumer
from kafkaworker.core.utils.asyncio_signals import wait_for_shutdown_signal

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "start example events consumer"

    def handle(self, *args, **options):
        logger.info("starting example-topic consumer")
        asyncio.run(self.__run_consumer())

    async def __run_consumer(self) -> None:
        consumer = ExampleEventKafkaConsumer()
        consumer_task = asyncio.create_task(consumer.run())

        async def shutdown() -> None:
            await self.__shutdown_consumer(consumer, consumer_task)

        await wait_for_shutdown_signal(on_shutdown=shutdown)

    async def __shutdown_consumer(
        self,
        consumer: ExampleEventKafkaConsumer,
        consumer_task: asyncio.Task,
    ) -> None:
        logger.info("shutdown signal received; stopping example-topic consumer")
        consumer.request_shutdown()
        await consumer_task
        logger.info("example-topic consumer stopped")
