import logging
from aiohttp import ClientSession
import time
from typing import AsyncIterator

logger = logging.getLogger(__name__)

CHUNK_SIZE = 10 * 1024 * 1024 # 10MB

class FileDownloaderService:
  def __init__(self, ttl: int = 25):
    self.ttl = ttl
    self.session: ClientSession | None = None
    self.connection_expires_at = None

  async def download_file(self, file_url: str) -> tuple[AsyncIterator[bytes], str]:
    session = await self._get_session()
    response = await session.request(method="GET", url=file_url)
    file_extension = response.content_type.split("/")[-1]

    async def stream_with_cleanup():
      try:
        async for chunk in response.content.iter_chunked(CHUNK_SIZE):
          yield chunk
      finally:
        logger.info(f"[FileDownloaderService] Closing response for {file_url}")
        response.close()
    
    return stream_with_cleanup(), file_extension

  async def _get_session(self):
    if (
      self.session is None
      or time.monotonic() > self.connection_expires_at
    ):
      if self.session is not None:
        logger.info(f"[FileDownloaderService] Closing old session")
        await self.session.close()

      self.connection_expires_at = time.monotonic() + self.ttl
      self.session = ClientSession()

    time_left = self.connection_expires_at - time.monotonic()
    logger.info(
      f"[FileDownloaderService] Using existing HTTP session with TTL {time_left} seconds"
    )
    return self.session