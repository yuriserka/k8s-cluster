# Kafka Worker

Django app (Python **3.11**): **API** (HTTP + S3), **scheduler** (APScheduler / Postgres), **example-topic consumer** (Kafka → handlers). Shared logic in `kafkaworker/core`.

## Containers

| Container | README | Role |
|-----------|--------|------|
| API | [kafkaworker/containers/api/README.md](kafkaworker/containers/api/README.md) | REST/ASGI API, fetch-image, update-event |
| Scheduler | [kafkaworker/containers/scheduler/README.md](kafkaworker/containers/scheduler/README.md) | Scheduled DB jobs |
| Example-topic consumer | [kafkaworker/containers/example_events_worker/README.md](kafkaworker/containers/example_events_worker/README.md) | Kafka consumer for `example-topic` |

Each README covers **run** (env vars), **tests**, and **lint**. All three use the same [`Dockerfile`](Dockerfile) (multi-stage: deps → test/lint → runtime).

**Database migrations** are not a separate container; run `python manage.py migrate` with the API image (compose or pipeline `dev-migrate`). See [API README](kafkaworker/containers/api/README.md#option-a--docker-compose-api--postgres--kafka--localstack).

## Quick start (all services locally)

From this directory:

```bash
docker compose up --build
```

| Service | URL / port |
|---------|------------|
| API | http://localhost:8000 |
| Scheduler | port 8006 (process only) |
| Consumer | port 8005 (process only) |
| Postgres | localhost:5432 |
| Kafka | localhost:9092 |
| LocalStack | localhost:4566 |

Create Kafka topic `example-topic` — [Kafka infra README](../infra/kafka/README.md).

**Port note:** Do not run [kafka-producer](../kafka-producer/compose.yaml) at the same time on **5432** / **9092**.

**Vault files for compose:**

| File | Used by |
|------|---------|
| [`resources/vault/_admin/grafana/dev/.env`](../resources/vault/_admin/grafana/dev/.env) | API, scheduler, consumer (OTLP) |
| [`resources/vault/_admin/aws/dev/.env`](../resources/vault/_admin/aws/dev/.env) | LocalStack (`LOCALSTACK_AUTH_TOKEN`) |

Copy from the matching `.env.example` files before first run.

## Grafana / OpenTelemetry (compose)

Compose loads OTLP settings from `resources/vault/_admin/grafana/dev/.env` (copy from [`.env.example`](../resources/vault/_admin/grafana/dev/.env.example); set `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS` from Grafana Cloud → OpenTelemetry → Configure).

```bash
docker compose up -d --build
```

- Commands use `opentelemetry-instrument` (see [`compose.yaml`](compose.yaml)).
- Service names: `kafka-worker-api`, `kafka-worker-scheduler`, `kafka-worker-example-topic-consumer`.
- Image defaults disable export (`OTEL_*_EXPORTER=none`); vault + compose env enable Grafana.
- Log correlation: [`kafkaworker/config/telemetry.py`](kafkaworker/config/telemetry.py) and [`trace_context.py`](kafkaworker/core/logging/trace_context.py).

To disable telemetry locally, unset vault OTLP values or set `KAFKA_WORKER_LOG_TRACE_CONTEXT_ENABLED=false`.

## Full pipeline (cluster)

```bash
cd scripts
python pipeline_parser.py kafka-worker
```

See [scripts/README.md](../scripts/README.md).

## Repo-wide tasks

From `apps/kafka-worker/`:

| Step | Command |
|------|---------|
| Venv | `python3 -m venv .venv && . .venv/bin/activate` |
| Install | `pip install -r requirements.txt -r requirements_dev.txt` |
| Lint | `python -m flake8 kafkaworker` |
| Test | `export $(cat ./db-credentials) && python -Wa manage.py test` *(pipeline Postgres on **5433**)* |
| Docker build | `docker build -t kafka-worker-local:latest .` *(runs unit tests + flake8 in builder stage)* |

## End-to-end test (with producer)

1. Start kafka-producer compose and produce events — [kafka-producer README](../kafka-producer/README.md).
2. Start kafka-worker compose (or deploy to `dev`).
3. Port-forward API if needed: `minikube kubectl -- port-forward -n dev deployment/kafka-worker-api-dev 8000:8000`
4. Verify consumer logs and `example_events` in Postgres — [consumer README](kafkaworker/containers/example_events_worker/README.md#end-to-end-check).
