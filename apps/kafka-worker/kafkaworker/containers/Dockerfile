# syntax=docker/dockerfile:1
ARG CONTAINER=api

FROM python:3.11.7-slim AS deps
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install opentelemetry-distro opentelemetry-exporter-otlp \
    && opentelemetry-bootstrap --action=install

FROM python:3.11.7-slim AS runtime
ARG CONTAINER
WORKDIR /app

COPY --from=deps /opt/venv /opt/venv
COPY kafkaworker /app/kafkaworker
COPY manage.py worker_health_check.py /app/
RUN chmod +x /app/worker_health_check.py

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=kafkaworker.config.settings

ENV OTEL_SERVICE_NAME=kafka-worker-${CONTAINER}
ENV OTEL_TRACES_EXPORTER=none
ENV OTEL_METRICS_EXPORTER=none
ENV OTEL_LOGS_EXPORTER=none
ENV OTEL_RESOURCE_ATTRIBUTES="service.name=kafka-worker-${CONTAINER},service.namespace=local,deployment.environment=local"
