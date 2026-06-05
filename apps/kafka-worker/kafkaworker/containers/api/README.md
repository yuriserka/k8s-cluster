# API container (`kafka-worker-api`)

Django ASGI app (Gunicorn + Uvicorn workers): HTTP endpoints for hello-world, image fetch (S3 via LocalStack), and example-event updates. Shared domain code lives under `kafkaworker/core`.

**Prerequisites:** Python **3.11**, run commands from the [kafka-worker](../../../) app root (`apps/kafka-worker/`).

For minikube image builds, load Docker into minikube first — see [project README](../../../../../README.md#startingstoping).

---

## Run the container

### Option A — Docker Compose (API + Postgres + Kafka + LocalStack)

Built from shared [`Dockerfile.dev`](../Dockerfile.dev) with `CONTAINER=api`; API service in [`compose.yaml`](../../../compose.yaml):

```bash
docker compose up api --build
```

Defaults from [`default.yaml`](../../config/default.yaml) and compose: Postgres `postgres:5432`, LocalStack `http://localstack:4566`.

API: `http://localhost:8000`

Apply migrations before first use (same image):

```bash
docker compose run --rm api python manage.py migrate
```

### Option B — Local venv (no Docker)

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

export DJANGO_SETTINGS_MODULE=kafkaworker.config.settings
export DATABASE_HOST=localhost
export DATABASE_USER=ysdcr
export DATABASE_PASSWORD=ysdcr
export DATABASE_NAME=kafka-worker
export DATABASE_PORT=5432

python manage.py migrate
opentelemetry-instrument python -m gunicorn kafkaworker.asgi:application \
  -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Omit `opentelemetry-instrument` when OTLP is not configured.

### Option C — Cluster (`dev` namespace)

Pipeline: `dev-publish-api`, `dev-migrate`, `dev-deploy-api`.

```bash
minikube kubectl -- port-forward -n dev deployment/kafka-worker-api-dev 8000:8000
```

### Environment variables

| Variable | Required | Example (compose) | Example (cluster `dev`) | Notes |
|----------|----------|-------------------|-------------------------|--------|
| `DJANGO_SETTINGS_MODULE` | yes | `kafkaworker.config.settings` | same | Set in compose / image |
| `DATABASE_HOST` | yes | `postgres` | `postgresql` | |
| `DATABASE_PORT` | no | `5432` | `5432` | From `default.yaml` if unset |
| `DATABASE_NAME` | yes | `kafka-worker` | `kafka-worker` | |
| `DATABASE_USER` | yes | `ysdcr` | from vault | |
| `DATABASE_PASSWORD` | yes | `ysdcr` | from vault | |
| `AWS_ENDPOINT_URL` | yes | `http://localstack:4566` | `http://localstack:4566` | S3-compatible API |
| `AWS_ACCESS_KEY_ID` | yes | `test` | `test` | LocalStack |
| `AWS_SECRET_ACCESS_KEY` | yes | `test` | `test` | |
| `AWS_DEFAULT_REGION` | no | `us-east-1` | `us-east-1` | |
| `OTEL_SERVICE_NAME` | no | `kafka-worker-api` | from deploy | Compose override |
| `OTEL_EXPORTER_OTLP_*` | for Grafana | vault `.env` | vault | See [kafka-worker README](../../../README.md#grafana--opentelemetry-compose) |
| `KAFKA_WORKER_LOG_TRACE_CONTEXT_ENABLED` | no | `true` | `true` | [`telemetry.py`](../../config/telemetry.py) |

LocalStack Pro token: [`resources/vault/_admin/aws/dev/.env`](../../../../../resources/vault/_admin/aws/dev/.env) (compose `localstack` service).

Helm overrides: [`kube/dev/api.yaml`](../../../kube/dev/api.yaml).

### Try it

```bash
curl http://localhost:8000/hello-world

curl 'http://localhost:8000/fetch-image?url=https://example.com/image.jpg' \
  -H 'X-Request-ID: my-request-1'

# After consumer/producer flow created an event:
curl -X PATCH 'http://localhost:8000/update-event/<event_id>' \
  -H 'Content-Type: application/json' \
  -d '{"status":"processed"}'
```

Prometheus metrics: `http://localhost:8000/metrics`

---

## Tests

Shared Django test suite (not isolated to this package). Uses **Testcontainers Postgres** — Docker required. See [kafka-worker README](../../../README.md#tests-testcontainers).

```bash
. .venv/bin/activate
pip install -r requirements.txt -r requirements_dev.txt

python run_tests.py
```

Run lint and tests on the host or via [`.pipeline`](../../../.pipeline) — not during `docker build`.

---

## Lint

Project-wide lint + style — see [kafka-worker README](../../../README.md#quality-reports):

```bash
. .venv/bin/activate
pip install -r requirements_dev.txt
python code_checks.py
```
