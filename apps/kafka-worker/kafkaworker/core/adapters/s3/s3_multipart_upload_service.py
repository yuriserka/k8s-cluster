import logging
from typing import AsyncIterator


logger = logging.getLogger(__name__)

PART_SIZE = 10 * 1024 * 1024 # 10MB

class S3MultipartUploaderService:
  async def upload_file(
    self,
    s3_client,
    data_stream: AsyncIterator[bytes],
    bucket: str,
    key: str
  ):
    upload_id = await self._create_mpu(s3_client, bucket, key)
    logger.info(f"[S3MultipartUploaderService] created mpu for {key}")
    try:
      parts = await self._upload_file_parts(s3_client, data_stream, bucket, key, upload_id)
      await self._complete_mpu(s3_client, bucket, key, upload_id, parts)
      return f"s3://{bucket}/{key}"
    except Exception as e:
      await self._cancel_mpu(s3_client, bucket, key, upload_id)
      logger.error(f"[S3MultipartUploaderService] failed to complete mpu for {key} // {upload_id}. {e}")
      raise Exception(f"Upload failed: {str(e)}") from e

  async def _upload_file_parts(
    self,
    s3_client,
    data_stream: AsyncIterator[bytes],
    bucket: str,
    key: str,
    upload_id: str
  ):
    parts = []
    part_number = 1
    buffer = bytearray()

    async for chunk in data_stream:
      buffer.extend(chunk)
      while len(buffer) >= PART_SIZE:
        part_data = bytes(buffer[:PART_SIZE])
        buffer = buffer[PART_SIZE:]

        part = await s3_client.upload_part(
            Bucket=bucket,
            Key=key,
            PartNumber=part_number,
            UploadId=upload_id,
            Body=part_data
        )

        logger.info(f"[S3MultipartUploaderService] part {part_number} for {key} // {upload_id}")

        parts.append({
          'ETag': part['ETag'],
          'PartNumber': part_number
        })
        part_number += 1

    if buffer:
      part = await s3_client.upload_part(
        Bucket=bucket,
        Key=key,
        PartNumber=part_number,
        UploadId=upload_id,
        Body=bytes(buffer)
      )
      logger.info(f"[S3MultipartUploaderService] final part {part_number} for {key} // {upload_id}")
      parts.append({
        'ETag': part['ETag'],
        'PartNumber': part_number
      })

    return parts

  async def _create_mpu(
    self,
    s3_client,
    bucket: str,
    key: str
  ):
    mpu = await s3_client.create_multipart_upload(Bucket=bucket, Key=key)
    return mpu['UploadId']

  async def _cancel_mpu(
    self,
    s3_client,
    bucket: str,
    key: str,
    upload_id: str
  ):
    await s3_client.abort_multipart_upload(
      Bucket=bucket,
      Key=key,
      UploadId=upload_id
    )

  async def _complete_mpu(
    self,
    s3_client,
    bucket: str,
    key: str,
    upload_id: str,
    parts: list
  ):
    await s3_client.complete_multipart_upload(
      Bucket=bucket,
      Key=key,
      UploadId=upload_id,
      MultipartUpload={'Parts': parts}
    )
