"""OpenTelemetry and log trace-context settings (via Pconf)."""

from __future__ import annotations

from kafkaworker.config import config


def _config_bool(name: str, default: bool = True) -> bool:
    value = config.get(name)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _config_str(name: str, default: str = '') -> str:
    value = config.get(name)
    if value is None:
        return default
    return str(value).strip()


def is_log_trace_context_enabled() -> bool:
    return _config_bool('KAFKA_WORKER_LOG_TRACE_CONTEXT_ENABLED', default=True)


def is_otel_traces_export_configured() -> bool:
    exporter = _config_str('OTEL_TRACES_EXPORTER', 'none').lower()
    if exporter in ('', 'none', 'false', 'off'):
        return False
    endpoint = _config_str('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT') or _config_str(
        'OTEL_EXPORTER_OTLP_ENDPOINT'
    )
    return bool(endpoint)
