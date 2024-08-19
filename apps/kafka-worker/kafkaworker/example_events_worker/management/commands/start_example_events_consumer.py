import asyncio
from django.core.management.base import BaseCommand

from kafkaworker.example_events_worker.example_events_consumer import ExampleEventKafkaConsumer
from kafkaworker.core.services.example_events_service import ExampleEventsService


class Command(BaseCommand):
    help = 'start example events consumer'

    def handle(self, *args, **options):
        consumer = ExampleEventKafkaConsumer(
            example_events_service=ExampleEventsService()
        )

        asyncio.run(consumer.run())
