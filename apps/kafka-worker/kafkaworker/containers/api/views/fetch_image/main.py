from django.http import HttpResponse, JsonResponse, HttpRequest, HttpResponseBadRequest
from kafkaworker.core.adapters.s3.s3_adapter import S3Adapter
from kafkaworker.core.adapters.s3.s3_multipart_upload_service import S3MultipartUploaderService
from kafkaworker.core.services.file_downloader_service import FileDownloaderService
from kafkaworker.core.services.media_processing_service import MediaProcessingService
import logging
import uuid

from django.views import View

logger = logging.getLogger(__name__)

media_processing_service = MediaProcessingService(
  file_downloader_service=FileDownloaderService(),
  s3_adapter=S3Adapter(
    s3_multipart_upload_service=S3MultipartUploaderService(),
  ),
)

class FetchImageView(View):
  async def get(self, request: HttpRequest) -> HttpResponse:
    query_params = request.GET
    url = query_params.get('url')
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    if url:
      logger.info(f"Fetching image from {url} with request id {request_id}")
      try:
        url = await media_processing_service.process_media(url, request_id)
        return JsonResponse({'request_id': request_id, 'url': url})
      except Exception as e:
        logger.error(f"Error fetching image from {url} with request id {request_id}: {e}")
        return HttpResponseBadRequest('Error fetching image')

    return HttpResponseBadRequest('Missing url query parameter')
