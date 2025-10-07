from contextlib import asynccontextmanager
import logging
from typing import AsyncIterator
import aioboto3
import gc
import time

from kafkaworker.config import config
from kafkaworker.core.adapters.s3.s3_multipart_upload_service import S3MultipartUploaderService

logger = logging.getLogger(__name__)


class S3Adapter:
  def __init__(self, s3_multipart_upload_service: S3MultipartUploaderService, ttl: int = 40):
    self.ttl = ttl
    self.session: aioboto3.Session = None
    self.connection_expires_at = None
    self.s3_multipart_upload_service = s3_multipart_upload_service

  async def upload_file(
    self,
    file_content: AsyncIterator[bytes],
    key: str,
    bucket_name: str,
  ) -> str:
    logger.info(f"Uploading file {key} to bucket {bucket_name}")
    try:
      async with self._get_s3_client() as s3:
        url = await self.s3_multipart_upload_service.upload_file(
          s3, 
          file_content, 
          bucket_name, 
          key
        )
      logger.info(f"File {key} uploaded to bucket {bucket_name} with url {url}")
      return url
    except Exception as e:
      logger.error(f"Error uploading file {key} to bucket {bucket_name}: {e}")
      raise

  @asynccontextmanager
  async def _get_s3_client(self):
    client = self._get_session().client('s3', endpoint_url=config.get('AWS_ENDPOINT_URL'))
    async with client as s3:
      try:
        yield s3
      finally:
        gc.collect()

  def _get_session(self):
    if (
      self.session is None
      or time.monotonic() > self.connection_expires_at
    ):
      self.connection_expires_at = time.monotonic() + self.ttl
      self.session = aioboto3.Session()

    time_left = self.connection_expires_at - time.monotonic()
    logger.info(f"[S3Adapter] Using existing S3 session with TTL {time_left} seconds")
    return self.session