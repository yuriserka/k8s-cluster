FROM python:3.11.7-slim AS compile-image
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install opentelemetry-distro
RUN pip install opentelemetry-exporter-otlp
RUN opentelemetry-bootstrap --action=install

FROM python:3.11.7-slim AS build-image
COPY --from=compile-image /opt/venv /opt/venv

WORKDIR /app
COPY . .

RUN chmod +x /app/worker_health_check.py

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=kafkaworker.config.settings

ENV PATH="/opt/venv/bin:$PATH"

# OTLP export off by default (enable via env + resources/vault/_admin/grafana/<env>/.env).
# Avoids Grafana Cloud 429 rate limits during local compose.
ENV OTEL_SERVICE_NAME=kafka-worker
ENV OTEL_TRACES_EXPORTER=none
ENV OTEL_METRICS_EXPORTER=none
ENV OTEL_LOGS_EXPORTER=none
