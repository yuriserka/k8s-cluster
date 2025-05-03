import asyncio
import logging
from django.core.management.base import BaseCommand

from kafkaworker.example_events_worker.example_events_consumer import ExampleEventKafkaConsumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'start example events consumer'

    def handle(self, *args, **options):
        consumer = ExampleEventKafkaConsumer()
        logger.info("starting example-topic consumer")
        asyncio.run(consumer.run())
