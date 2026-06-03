from django.utils.deprecation import MiddlewareMixin

from kafkaworker.config.telemetry import (
    is_log_trace_context_enabled,
    is_otel_traces_export_configured,
)
from kafkaworker.core.logging.trace_context import (
    bind_mock_trace_context,
    reset_trace_context,
)


class MockTraceContextMiddleware(MiddlewareMixin):
    """Bind mock trace_id/span_id per HTTP request when OTLP traces are not configured."""

    def _use_mock_per_request(self) -> bool:
        return (
            is_log_trace_context_enabled()
            and not is_otel_traces_export_configured()
        )

    def process_request(self, request):
        if self._use_mock_per_request():
            bind_mock_trace_context()

    def process_response(self, request, response):
        if self._use_mock_per_request():
            reset_trace_context()
        return response

    def process_exception(self, request, exception):
        if self._use_mock_per_request():
            reset_trace_context()
        return None
