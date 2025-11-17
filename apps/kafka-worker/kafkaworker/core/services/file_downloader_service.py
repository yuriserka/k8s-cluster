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

  def __del__(self):
    if self.session is not None:
      logger.info(f"[FileDownloaderService] cleaning up session")
      self.session.close()

  async def download_file_content(self, file_url: str):
    session = await self._get_session()
    response = await session.request(method="GET", url=file_url)
    return response.content

  async def download_file(self, file_url: str) -> AsyncIterator[bytes]:
    session = await self._get_session()
    response = await session.request(method="GET", url=file_url)

    async def generator():
      try:
        async for chunk in response.content.iter_chunked(CHUNK_SIZE):
          yield chunk
      finally:
        logger.info(f"[FileDownloaderService] Closing response for {file_url}")
        response.close()

      return generator()

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