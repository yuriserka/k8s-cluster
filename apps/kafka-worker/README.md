# Kafka Worker

Django app (Python **3.11**): **API** (HTTP + S3), **scheduler** (APScheduler / Postgres), **example-topic consumer** (Kafka → handlers). Shared logic in `kafkaworker/core`.

## Containers

| Container | README | Role |
|-----------|--------|------|
| API | [kafkaworker/containers/api/README.md](kafkaworker/containers/api/README.md) | REST/ASGI API, fetch-image, update-event |
| Scheduler | [kafkaworker/containers/scheduler/README.md](kafkaworker/containers/scheduler/README.md) | Scheduled DB jobs |
| Example-topic consumer | [kafkaworker/containers/example_events_worker/README.md](kafkaworker/containers/example_events_worker/README.md) | Kafka consumer for `example-topic` |

Each README covers **run** (env vars), **tests**, and **lint**. All three use shared [`Dockerfile.dev`](kafkaworker/containers/Dockerfile.dev) / [`Dockerfile`](kafkaworker/containers/Dockerfile) with `CONTAINER` build arg (`api`, `scheduler`, `example-topic-consumer`). Lint and tests run via [`.pipeline`](.pipeline) or on the host — not during `docker build`.

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

- [`docker-entrypoint.sh`](kafkaworker/containers/docker-entrypoint.sh) wraps commands with `opentelemetry-instrument` when vault sets `OTEL_EXPORTER_OTLP_ENDPOINT` (see [`compose.yaml`](compose.yaml)).
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
| Lint + style (black + flake8) | `python code_checks.py` |
| Test + coverage | `python run_tests.py` |
| Docker build (api) | `docker build -t kafka-worker-api-local:latest -f kafkaworker/containers/Dockerfile.dev --build-arg CONTAINER=api .` |
| Docker build (scheduler) | `docker build -t kafka-worker-scheduler-local:latest -f kafkaworker/containers/Dockerfile.dev --build-arg CONTAINER=scheduler .` |
| Docker build (consumer) | `docker build -t kafka-worker-example-topic-consumer-local:latest -f kafkaworker/containers/Dockerfile.dev --build-arg CONTAINER=example-topic-consumer .` |

### Quality reports

After `python code_checks.py`:

| Report | Path |
|--------|------|
| black (stdout on failure) | — |
| flake8 (stdout) | — |

After `python run_tests.py`:

| Report | Path |
|--------|------|
| Coverage HTML | `reports/coverage/html/index.html` |
| Coverage XML | `reports/coverage/coverage.xml` |

Minimum line coverage is enforced at **8%** (`fail_under` in [`.coveragerc`](.coveragerc)); raise the floor as tests grow.

Shared [`Dockerfile.dev`](kafkaworker/containers/Dockerfile.dev) builds runtime images only — no lint or tests during `docker build`. Run `code_checks.py` and `run_tests.py` on the host (or via [`.pipeline`](.pipeline)) when you want those gates.

### Tests (Testcontainers)

Tests start a **Postgres container via Testcontainers** ([Python docs](https://testcontainers-python.readthedocs.io/en/latest/)) — no external database or `db-credentials` file is required. Docker must be running.

```bash
. .venv/bin/activate
pip install -r requirements.txt -r requirements_dev.txt
python run_tests.py
```

`run_tests.py` runs `manage.py test` with coverage report and verification. `manage.py test` automatically uses [`test_settings.py`](kafkaworker/config/test_settings.py) (Testcontainers Postgres). Other commands use production settings.

**WSL + Docker Desktop:** If the Unix socket fails, enable **“Expose daemon on tcp://localhost:2375 without TLS”** in Docker Desktop → Settings → General and set `export DOCKER_HOST=tcp://localhost:2375`.

**Minikube docker-env:** Testcontainers/Ryuk needs Docker Desktop, not minikube’s Docker. [`postgres_testcontainer.py`](kafkaworker/tests/postgres_testcontainer.py) and [`pipeline_parser.py`](../../scripts/pipeline_parser.py) detect minikube docker-env and switch to `DOCKER_HOST=unix:///var/run/docker.sock` for tests.

## End-to-end test (with producer)

1. Start kafka-producer compose and produce events — [kafka-producer README](../kafka-producer/README.md).
2. Start kafka-worker compose (or deploy to `dev`).
3. Port-forward API if needed: `minikube kubectl -- port-forward -n dev deployment/kafka-worker-api-dev 8000:8000`
4. Verify consumer logs and `example_events` in Postgres — [consumer README](kafkaworker/containers/example_events_worker/README.md#end-to-end-check).
