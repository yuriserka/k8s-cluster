from django.utils.deprecation import MiddlewareMixin

from kafkaworker.core.logging.trace_context import (
    bind_mock_trace_context,
    reset_trace_context,
)


class MockTraceContextMiddleware(MiddlewareMixin):
    """Assign mock trace_id/span_id per HTTP request so logs can be correlated."""

    def process_request(self, request):
        bind_mock_trace_context()

    def process_response(self, request, response):
        reset_trace_context()
        return response

    def process_exception(self, request, exception):
        reset_trace_context()
        return None
