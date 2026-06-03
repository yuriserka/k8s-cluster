import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch

from kafkaworker.config import config
from kafkaworker.config import telemetry
from kafkaworker.core.logging import trace_context as tc


def _telemetry_config(**overrides):
    base = {
        'KAFKA_WORKER_LOG_TRACE_CONTEXT_ENABLED': True,
        'OTEL_TRACES_EXPORTER': 'none',
        'OTEL_EXPORTER_OTLP_ENDPOINT': '',
        'OTEL_EXPORTER_OTLP_TRACES_ENDPOINT': '',
    }
    base.update(overrides)
    return base


class TraceContextTestCase(TestCase):
    def setUp(self):
        tc.reset_trace_context()

    def tearDown(self):
        tc.reset_trace_context()

    @patch.dict(config, _telemetry_config(KAFKA_WORKER_LOG_TRACE_CONTEXT_ENABLED=False))
    def test_disabled_returns_dash(self):
        tc.bind_mock_trace_context()
        self.assertEqual(tc.get_trace_id(), '-')
        self.assertEqual(tc.get_span_id(), '-')

    @patch.dict(config, _telemetry_config())
    def test_mock_mode_uses_contextvars(self):
        tc.bind_mock_trace_context()
        trace_id = tc.get_trace_id()
        span_id = tc.get_span_id()
        self.assertEqual(len(trace_id), 32)
        self.assertEqual(len(span_id), 16)
        self.assertTrue(all(c in '0123456789abcdef' for c in trace_id))
        self.assertTrue(all(c in '0123456789abcdef' for c in span_id))

    @patch.dict(
        config,
        _telemetry_config(
            OTEL_TRACES_EXPORTER='otlp',
            OTEL_EXPORTER_OTLP_ENDPOINT='https://otlp.example/otlp',
        ),
    )
    @patch.object(tc, 'trace')
    def test_otlp_mode_reads_active_span(self, mock_trace_module):
        mock_ctx = MagicMock()
        mock_ctx.is_valid = True
        mock_ctx.trace_id = int('a' * 32, 16)
        mock_ctx.span_id = int('b' * 16, 16)
        mock_trace_module.get_current_span.return_value.get_span_context.return_value = (
            mock_ctx
        )

        self.assertEqual(tc.get_trace_id(), 'a' * 32)
        self.assertEqual(tc.get_span_id(), 'b' * 16)

    @patch.dict(
        config,
        _telemetry_config(
            OTEL_TRACES_EXPORTER='otlp',
            OTEL_EXPORTER_OTLP_ENDPOINT='https://otlp.example/otlp',
        ),
    )
    @patch.object(tc, 'trace')
    def test_otlp_mode_invalid_span_returns_dash(self, mock_trace_module):
        mock_ctx = MagicMock()
        mock_ctx.is_valid = False
        mock_trace_module.get_current_span.return_value.get_span_context.return_value = (
            mock_ctx
        )

        self.assertEqual(tc.get_trace_id(), '-')
        self.assertEqual(tc.get_span_id(), '-')

    @patch.dict(config, _telemetry_config())
    def test_work_unit_mock_context_manager(self):
        self.assertIsNone(tc._trace_id.get())
        with tc.work_unit_trace_context('test.unit'):
            self.assertIsNotNone(tc._trace_id.get())
        self.assertIsNone(tc._trace_id.get())

    @patch.dict(
        config,
        _telemetry_config(
            OTEL_TRACES_EXPORTER='otlp',
            OTEL_EXPORTER_OTLP_ENDPOINT='https://otlp.example/otlp',
        ),
    )
    @patch.object(tc, 'trace')
    def test_work_unit_otlp_creates_span(self, mock_trace_module):
        mock_tracer = MagicMock()
        mock_trace_module.get_tracer.return_value = mock_tracer
        mock_span_cm = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span_cm

        with tc.work_unit_trace_context('kafka.consume'):
            pass

        mock_tracer.start_as_current_span.assert_called_once_with('kafka.consume')
        mock_span_cm.__enter__.assert_called_once()
        mock_span_cm.__exit__.assert_called_once()

    @patch.dict(config, _telemetry_config())
    def test_trace_context_filter_injects_fields(self):
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='hello',
            args=(),
            exc_info=None,
        )
        filt = tc.TraceContextFilter()
        tc.bind_mock_trace_context()
        self.assertTrue(filt.filter(record))
        self.assertEqual(len(record.trace_id), 32)
        self.assertEqual(len(record.span_id), 16)

    @patch.dict(
        config,
        _telemetry_config(
            OTEL_TRACES_EXPORTER='otlp',
            OTEL_EXPORTER_OTLP_ENDPOINT='',
        ),
    )
    def test_is_otel_traces_export_configured_requires_endpoint(self):
        self.assertFalse(telemetry.is_otel_traces_export_configured())
