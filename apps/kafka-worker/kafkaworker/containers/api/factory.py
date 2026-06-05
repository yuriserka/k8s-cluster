from kafkaworker.core.models.example_event.example_event_repository import ExampleEventRepository
from kafkaworker.core.services.example_events_service import ExampleEventsService
from kafkaworker.core.services.media_processing_service import MediaProcessingService
from kafkaworker.core.services.file_downloader_service import FileDownloaderService
from kafkaworker.core.adapters.s3.s3_adapter import S3Adapter
from kafkaworker.core.adapters.s3.s3_multipart_upload_service import S3MultipartUploaderService

media_processing_service = MediaProcessingService(
    file_downloader_service=FileDownloaderService(),
    s3_adapter=S3Adapter(
        s3_multipart_upload_service=S3MultipartUploaderService(),
    ),
)

example_events_service = ExampleEventsService(example_event_repository=ExampleEventRepository())
