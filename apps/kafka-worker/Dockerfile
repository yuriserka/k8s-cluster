FROM python:3.11.7-slim AS deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install opentelemetry-distro opentelemetry-exporter-otlp \
    && opentelemetry-bootstrap --action=install

FROM python:3.11.7-slim AS runtime
WORKDIR /app

COPY --from=deps /opt/venv /opt/venv
COPY kafkaworker /app/kafkaworker
COPY manage.py /app/manage.py
COPY worker_health_check.py /app/worker_health_check.py
RUN chmod +x /app/worker_health_check.py

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=kafkaworker.config.settings

ENV OTEL_SERVICE_NAME=kafka-worker
ENV OTEL_TRACES_EXPORTER=none
ENV OTEL_METRICS_EXPORTER=none
ENV OTEL_LOGS_EXPORTER=none
ENV OTEL_RESOURCE_ATTRIBUTES="service.name=kafka-worker,service.namespace=local,deployment.environment=local"
