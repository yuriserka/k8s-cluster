# Example-topic consumer (`kafka-worker-example-topic-consumer`)

Async Kafka consumer for `example-topic`: processes messages from [kafka-producer](../../../../../kafka-producer/README.md) (weather reports, user messages), persists/handlers via `kafkaworker/core`, uses LocalStack for S3 when needed.

Entry: `manage.py start_example_events_consumer` → [`example_events_consumer.py`](example_events_consumer.py).

**Prerequisites:** Python **3.11**, run from [kafka-worker](../../../) app root.

For minikube image builds, see [project README](../../../../../README.md#startingstoping).

---

## Run the container

### Option A — Docker Compose

Built from shared [`Dockerfile.dev`](../Dockerfile.dev) with `CONTAINER=example-topic-consumer`.

```bash
docker compose up example-topic-consumer --build
```

Depends on **postgres**, **kafka**, and **localstack**. Create topic `example-topic` if empty — [Kafka infra README](../../../../../infra/kafka/README.md).

Host port **8005** (container health/metrics placeholder).

### Option B — Local venv

```bash
. .venv/bin/activate
export DJANGO_SETTINGS_MODULE=kafkaworker.config.settings
export DATABASE_HOST=localhost DATABASE_USER=ysdcr DATABASE_PASSWORD=ysdcr
export DATABASE_NAME=kafka-worker DATABASE_PORT=5432
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export KAFKA_CONSUMER_GROUP_ID=kafka-worker
export KAFKA_TOPICS_EXAMPLE_EVENTS=example-topic
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1

python manage.py migrate
python manage.py start_example_events_consumer
```

### Option C — Cluster (`dev`)

Pipeline: `dev-publish-kafka-worker`, `dev-deploy-kafka-worker`.

```bash
minikube kubectl -- logs -n dev -f deployment/kafka-worker-example-topic-consumer-dev
```

---

## Environment variables

| Variable | Required | Example (compose) | Example (cluster `dev`) | Notes |
|----------|----------|-------------------|-------------------------|--------|
| `DJANGO_SETTINGS_MODULE` | yes | `kafkaworker.config.settings` | same | |
| `DATABASE_*` | yes | see API README | `postgresql` host in cluster | |
| `KAFKA_BOOTSTRAP_SERVERS` | yes | `kafka:9092` | `kafka:9092` | |
| `KAFKA_CONSUMER_GROUP_ID` | yes | `kafka-worker` | `kafka-worker` | |
| `KAFKA_TOPICS_EXAMPLE_EVENTS` | yes | `example-topic` | `example-topic` | Override in compose |
| `AWS_ENDPOINT_URL` | yes | `http://localstack:4566` | same | |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | yes | `test` | `test` | |
| `AWS_DEFAULT_REGION` | no | `us-east-1` | `us-east-1` | |
| `OTEL_SERVICE_NAME` | no | `kafka-worker-example-topic-consumer` | deploy | |
| `OTEL_EXPORTER_OTLP_*` | for Grafana | vault | vault | [kafka-worker README](../../../README.md#grafana--opentelemetry-compose) |
| `KAFKA_WORKER_LOG_TRACE_CONTEXT_ENABLED` | no | `true` | `true` | Per-message trace via [`trace_context.py`](../../core/logging/trace_context.py) |

Helm overrides: [`kube/dev/example-topic-consumer.yaml`](../../../kube/dev/example-topic-consumer.yaml).

---

## End-to-end check

1. Start [kafka-producer](../../../../../kafka-producer/README.md) compose and produce to `example-topic`.
2. Start this consumer (compose or cluster).
3. Confirm logs show consumed messages and rows in Postgres:

```sql
SELECT * FROM public.example_events ee ORDER BY ee.created_at DESC;
```

---

## Tests

Same project suite — see [kafka-worker README](../../../README.md#quality-reports).

```bash
python run_tests.py
```

---

## Lint

```bash
python code_checks.py
```
