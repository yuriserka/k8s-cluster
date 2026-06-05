from django.http import HttpResponse, JsonResponse, HttpRequest, HttpResponseBadRequest
from kafkaworker.containers.api.factory import media_processing_service
import logging
import uuid

from django.views import View

logger = logging.getLogger(__name__)


class FetchImageView(View):
    async def get(self, request: HttpRequest) -> HttpResponse:
        query_params = request.GET
        url = query_params.get("url")
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        if url:
            logger.info(f"Fetching image from {url} with request id {request_id}")
            try:
                url = await media_processing_service.process_media(url, request_id)
                return JsonResponse({"request_id": request_id, "url": url})
            except Exception as e:
                logger.error(f"Error fetching image from {url} with request id {request_id}: {e}")
                return HttpResponseBadRequest("Error fetching image")

        return HttpResponseBadRequest("Missing url query parameter")
