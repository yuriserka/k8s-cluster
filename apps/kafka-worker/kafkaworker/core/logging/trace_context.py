from __future__ import annotations

import contextvars
import logging
import secrets

_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    'trace_id', default=None
)
_span_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    'span_id', default=None
)


def bind_mock_trace_context() -> None:
    """Set a new mock W3C-style trace_id (32 hex) and span_id (16 hex) for this context."""
    _trace_id.set(secrets.token_hex(16))
    _span_id.set(secrets.token_hex(8))


def reset_trace_context() -> None:
    _trace_id.set(None)
    _span_id.set(None)


def get_trace_id() -> str:
    v = _trace_id.get()
    return v if v is not None else '-'


def get_span_id() -> str:
    v = _span_id.get()
    return v if v is not None else '-'


class TraceContextFilter(logging.Filter):
    """Injects trace_id and span_id on each LogRecord for formatters."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        record.span_id = get_span_id()
        return True
