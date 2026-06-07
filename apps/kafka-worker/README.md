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

Start shared infra first from [`../infra/`](../infra/) on network **`k8s-cluster-local`**. Init script [`initdb/`](initdb/) creates database `kafka-worker` on first Postgres volume init (mounted by infra compose).

**Infra + this app:**

```bash
cd ../infra && docker compose up -d
cd ../kafka-worker
docker compose up --build
make migrate   # or: docker compose run --rm api python manage.py migrate
```

Or from `scripts/`: `make setup-infra MODE=compose`

**App services only** (when infra is already running):

```bash
docker compose up -d --build --no-deps api scheduler example-topic-consumer
```

| Service | Host port |
|---------|-----------|
| API | http://localhost:8000 |
| Scheduler | port 8006 |
| Consumer | port 8005 |
| Postgres | localhost:5432 (database `kafka-worker`; also `kafka-producer` if that stack started Postgres first) |
| Kafka | localhost:9092 |
| LocalStack | localhost:4566 |

Create Kafka topic `example-topic` — [Kafka infra README](../infra/kafka/README.md).

## Shared infra with kafka-producer

Both apps share network **`k8s-cluster-local`** and fixed container names. Start infra from [`../infra/`](../infra/) — see [infra README](../infra/README.md) and [kafka-producer README](../kafka-producer/README.md#shared-infra-with-kafka-worker).

[`initdb/`](initdb/) creates database `kafka-worker` only on **first** Postgres volume init. If [kafka-producer](../kafka-producer/README.md) started Postgres first on an existing volume, run `make migrate` after ensuring the DB exists, or use [`database create`](../../scripts/k8s_cluster/commands/database/service.py) in cluster workflows.

**Vault files for compose:**

| File | Used by |
|------|---------|
| [`resources/vault/_admin/grafana/dev/.env`](../resources/vault/_admin/grafana/dev/.env) | API, scheduler, consumer (OTLP) |
| [`resources/vault/_admin/aws/dev/.env`](../resources/vault/_admin/aws/dev/.env) | Infra LocalStack (`LOCALSTACK_AUTH_TOKEN`) |

Copy from the matching `.env.example` files before first run.

## Grafana / OpenTelemetry

### Compose (local)

Compose loads OTLP settings from `resources/vault/_admin/grafana/dev/.env` (copy from [`.env.example`](../resources/vault/_admin/grafana/dev/.env.example); set `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS` from Grafana Cloud → OpenTelemetry → Configure).

```bash
docker compose up -d --build
```

- [`docker-entrypoint.sh`](kafkaworker/containers/docker-entrypoint.sh) wraps commands with `opentelemetry-instrument` when vault sets `OTEL_EXPORTER_OTLP_ENDPOINT` (see [`compose.yaml`](compose.yaml)).
- Service names: `kafka-worker-api`, `kafka-worker-scheduler`, `kafka-worker-example-topic-consumer`.
- `service.namespace=local` in `OTEL_RESOURCE_ATTRIBUTES` ([`Dockerfile.dev`](kafkaworker/containers/Dockerfile.dev)).
- [`Dockerfile.dev`](kafkaworker/containers/Dockerfile.dev) installs unpinned OTel pip packages; image defaults disable export (`OTEL_*_EXPORTER=none`); vault enables Grafana.
- Log correlation: [`kafkaworker/config/telemetry.py`](kafkaworker/config/telemetry.py) and [`trace_context.py`](kafkaworker/core/logging/trace_context.py).

To disable telemetry locally, unset vault OTLP values or set `KAFKA_WORKER_LOG_TRACE_CONTEXT_ENABLED=false`.

### Cluster (`dev` namespace)

OpenTelemetry is injected at **publish time** by [`app publish`](../../scripts/k8s_cluster/commands/app/publish_service.py) when [`resources/kafka-worker-api/dev.yaml`](../../resources/kafka-worker-api/dev.yaml) (and scheduler/consumer) define:

```yaml
instrumentation:
  enabled: true
  pythonAgent:
    version: "0.63b1"
```

Pins `opentelemetry-distro`, runs `opentelemetry-bootstrap`, injects OTLP env from Grafana vault. Kube runs `/docker-entrypoint.sh` before app args ([`kube/dev/api.yaml`](kube/dev/api.yaml)). `service.namespace=dev` in cluster.

### Dockerfile.dev vs Dockerfile (pipeline)

| | [`Dockerfile.dev`](kafkaworker/containers/Dockerfile.dev) | [`Dockerfile`](kafkaworker/containers/Dockerfile) |
|--|--|--|
| Used by | Compose local builds | Pipeline / cluster publish |
| OTel pip | Unpinned in image | Injected at publish via `pythonAgent` |
| Entrypoint | `docker-entrypoint.sh` | `docker-entrypoint.sh` (base); OTel pip added by publish |

## Graceful shutdown

- **API:** Gunicorn `--graceful-timeout 30` / `--timeout 60` in compose and [`kube/dev/api.yaml`](kube/dev/api.yaml).
- **Scheduler / consumer:** SIGTERM handled via [`asyncio_signals.py`](kafkaworker/core/utils/asyncio_signals.py) — stop polling/scheduling cleanly.
- **Kubernetes:** `terminationGracePeriodSeconds: 60` in [`envs/dev/values.yaml`](../../envs/dev/values.yaml).

## Full pipeline (cluster)

```bash
cd scripts
make deploy-app kafka-worker
# or: python -m k8s_cluster pipeline run kafka-worker
```

See [scripts/README.md](../../scripts/README.md).

## Repo-wide tasks

From `apps/kafka-worker/`:

| Step | Command |
|------|---------|
| Makefile (all targets) | `make help` |
| Lint + test gate | `make check` |
| Migrate (compose Postgres) | `make migrate` |
| Venv | `python3 -m venv .venv && . .venv/bin/activate` or `make venv` |
| Install | `pip install -r requirements.txt -r requirements_dev.txt` or `make install` |
| Lint + style (black + flake8) | `python code_checks.py` or `make code-checks` |
| Format (black) | `make format` |
| Full pipeline (cluster) | `make pipeline` |
| Test + coverage | `python run_tests.py` or `make test` |
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

**Minikube docker-env:** Testcontainers/Ryuk needs Docker Desktop, not minikube’s Docker. [`postgres_testcontainer.py`](kafkaworker/tests/postgres_testcontainer.py) and [`pipeline run`](../../scripts/k8s_cluster/commands/pipeline/runner.py) detect minikube docker-env and switch to `DOCKER_HOST=unix:///var/run/docker.sock` for tests.

## End-to-end test (with producer)

1. Start kafka-producer compose and produce events — [kafka-producer README](../kafka-producer/README.md).
2. Start kafka-worker compose (or deploy to `dev`).
3. Port-forward API if needed: `minikube kubectl -- port-forward -n dev deployment/kafka-worker-api-dev 8000:8000`
4. Verify consumer logs and `example_events` in Postgres — [consumer README](kafkaworker/containers/example_events_worker/README.md#end-to-end-check).
