import random
import logging
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpRequest,
    HttpResponseBadRequest,
)
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from kafkaworker.containers.api.factory import example_events_service


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class UpdateEventView(View):
    async def put(self, _: HttpRequest, event_id: str) -> HttpResponse:
        if not event_id:
            return HttpResponseBadRequest('Missing event_id')

        try:
            random_number = random.uniform(1.0, 10000.0)
            logger.info(f'Updating event {event_id} with random number {random_number}')
            updated_event = await example_events_service.update_event_payload(
                event_id=event_id,
                new_attributes={
                    'random_number_from_api': random_number,
                }
            )
            logger.info(f'Event {event_id} updated successfully with random number {random_number}')
            return JsonResponse({
                'message': 'Event updated successfully',
                'event': updated_event.payload,
            })
        except Exception as e:
            logger.error(f'Error updating event {event_id}: {e}', exc_info=True)
            return HttpResponseBadRequest(f'Error updating event {event_id}')
