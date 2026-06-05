# Scheduler container (`kafka-worker-scheduler`)

Django management command `start_scheduler`: runs APScheduler jobs (e.g. `UpdateEventJob`) against Postgres. No public HTTP API; compose maps host **8006** for health/metrics if exposed later.

**Prerequisites:** Python **3.11**, run from [kafka-worker](../../../) app root.

For minikube image builds, see [project README](../../../../../README.md#startingstoping).

---

## Run the container

### Option A — Docker Compose

Built from shared [`Dockerfile.dev`](../Dockerfile.dev) with `CONTAINER=scheduler`.

```bash
docker compose up scheduler --build
```

Requires Postgres (and typically API/consumer having written `example_events`). Scheduler command: `python manage.py start_scheduler` (OTEL wrapping via [`docker-entrypoint.sh`](../docker-entrypoint.sh) when vault OTLP is configured).

### Option B — Local venv

```bash
. .venv/bin/activate
export DJANGO_SETTINGS_MODULE=kafkaworker.config.settings
export DATABASE_HOST=localhost DATABASE_USER=ysdcr DATABASE_PASSWORD=ysdcr
export DATABASE_NAME=kafka-worker DATABASE_PORT=5432

python manage.py migrate
python manage.py start_scheduler
```

### Option C — Cluster (`dev`)

Pipeline: `dev-publish-scheduler`, `dev-deploy-scheduler`.

```bash
minikube kubectl -- logs -n dev -f deployment/kafka-worker-scheduler-dev
```

---

## Environment variables

| Variable | Example (compose) | Example (cluster `dev`) | Notes |
|----------|-------------------|-------------------------|--------|
| `DJANGO_SETTINGS_MODULE` | `kafkaworker.config.settings` | same | |
| `DATABASE_HOST` | `postgres` | `postgresql` | |
| `DATABASE_PORT` | `5432` | `5432` | |
| `DATABASE_NAME` | `kafka-worker` | `kafka-worker` | |
| `DATABASE_USER` / `DATABASE_PASSWORD` | `ysdcr` | vault | |
| `OTEL_SERVICE_NAME` | `kafka-worker-scheduler` | deploy | |
| `OTEL_EXPORTER_OTLP_*` | vault grafana `.env` | vault | [kafka-worker README](../../../README.md#grafana--opentelemetry-compose) |
| `KAFKA_WORKER_LOG_TRACE_CONTEXT_ENABLED` | `true` | `true` | Log `trace_id` / `span_id` |

No Kafka or AWS env on this service (DB-only jobs).

Helm overrides: [`kube/dev/scheduler.yaml`](../../../kube/dev/scheduler.yaml).

---

## Code layout

| Path | Role |
|------|------|
| [`management/commands/start_scheduler.py`](management/commands/start_scheduler.py) | Entry command |
| [`scheduler.py`](scheduler.py) | APScheduler wiring |
| [`jobs/update_event_job.py`](jobs/update_event_job.py) | Periodic example-event updates |

---

## Tests

Same project suite as the API — see [kafka-worker README](../../../README.md#quality-reports).

```bash
. .venv/bin/activate
python run_tests.py
```

---

## Lint

```bash
python code_checks.py
```
