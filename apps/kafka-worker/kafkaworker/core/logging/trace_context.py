from __future__ import annotations

import contextvars
import logging
import secrets
from contextlib import contextmanager
from typing import Iterator

try:
    from opentelemetry import trace
except ImportError:
    trace = None  # type: ignore[assignment]

from kafkaworker.config.telemetry import (
    is_log_trace_context_enabled,
    is_otel_traces_export_configured,
)

_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    'trace_id', default=None
)
_span_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    'span_id', default=None
)


def _get_otel_trace_and_span_ids() -> tuple[str, str]:
    if trace is None:
        return '-', '-'
    ctx = trace.get_current_span().get_span_context()
    if not ctx.is_valid:
        return '-', '-'
    return format(ctx.trace_id, '032x'), format(ctx.span_id, '016x')


def bind_mock_trace_context() -> None:
    """Set a new mock W3C-style trace_id (32 hex) and span_id (16 hex) for this context."""
    _trace_id.set(secrets.token_hex(16))
    _span_id.set(secrets.token_hex(8))


def reset_trace_context() -> None:
    _trace_id.set(None)
    _span_id.set(None)


def get_trace_id() -> str:
    if not is_log_trace_context_enabled():
        return '-'
    if is_otel_traces_export_configured():
        trace_id, _ = _get_otel_trace_and_span_ids()
        return trace_id
    v = _trace_id.get()
    return v if v is not None else '-'


def get_span_id() -> str:
    if not is_log_trace_context_enabled():
        return '-'
    if is_otel_traces_export_configured():
        _, span_id = _get_otel_trace_and_span_ids()
        return span_id
    v = _span_id.get()
    return v if v is not None else '-'


@contextmanager
def work_unit_trace_context(span_name: str) -> Iterator[None]:
    if not is_log_trace_context_enabled():
        yield
        return
    if is_otel_traces_export_configured():
        if trace is None:
            yield
            return
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(span_name):
            yield
        return
    bind_mock_trace_context()
    try:
        yield
    finally:
        reset_trace_context()


class TraceContextFilter(logging.Filter):
    """Injects trace_id and span_id on each LogRecord for formatters."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        record.span_id = get_span_id()
        return True
