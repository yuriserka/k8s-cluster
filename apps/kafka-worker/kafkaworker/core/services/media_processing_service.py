from datetime import datetime

from kafkaworker.core.services.file_downloader_service import FileDownloaderService
from kafkaworker.core.adapters.s3.s3_adapter import S3Adapter
import logging

logger = logging.getLogger(__name__)


class MediaProcessingService:
  def __init__(
    self,
    file_downloader_service: FileDownloaderService,
    s3_adapter: S3Adapter,
  ):
    self.file_downloader_service = file_downloader_service
    self.s3_adapter = s3_adapter

  async def process_media_content(self, file_url: str, request_id: str):
    now = datetime.now()
    file_name = f"{request_id}-media-{now.strftime('%Y-%m-%d-%H-%M-%S')}.jpeg"
    file_content = await self.file_downloader_service.download_file_content(file_url)
    url = await self.s3_adapter.upload_file_object(file_content, file_name, "media")
    logger.info(f"[MediaProcessingService] file {file_name} uploaded to {url} with request id {request_id}")
    return url

  async def process_media(self, file_url: str, request_id: str):
    now = datetime.now()
    file_stream = await self.file_downloader_service.download_file(file_url)
    file_name = f"{request_id}-media-{now.strftime('%Y-%m-%d-%H-%M-%S')}.jpeg"
    url = await self.s3_adapter.upload_file(file_stream, file_name, "media")
    logger.info(f"[MediaProcessingService] file {file_name} uploaded to {url} with request id {request_id}")
    return url
