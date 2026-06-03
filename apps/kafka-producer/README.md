# Kafka Producer

Gradle multi-module app (Java **21**): **API** (HTTP → outbox), **scheduler** (outbox → Kafka), **migrate** (Flyway). Shared domain and persistence in `app/core`.

## Containers

| Container | README | Role |
|-----------|--------|------|
| API | [app/containers/api/README.md](app/containers/api/README.md) | REST API, outbox writes |
| Scheduler | [app/containers/scheduler/README.md](app/containers/scheduler/README.md) | Publishes outbox to Kafka |
| Migrate | [app/containers/migrate/README.md](app/containers/migrate/README.md) | Flyway migrations (one-shot) |

Each README covers **run** (env vars), **tests**, and **lint** for that piece.

## Quick start (all services locally)

From this directory, with [minikube docker-env](../../README.md#startingstoping) only if you build images for the cluster:

```bash
docker compose up --build
```

- API: http://localhost:8080  
- Scheduler actuator: http://localhost:8081/actuator/health  

Create Kafka topic `example-topic` — [Kafka infra README](../infra/kafka/README.md).

**Port note:** Compose binds Postgres `5432` and Kafka `9092` on the host. Do not run [kafka-worker](../kafka-worker/compose.yaml) at the same time on those ports.

## Grafana / OpenTelemetry (compose)

Compose loads OTLP credentials and exporter settings from the same vault file as kafka-worker:

`resources/vault/_admin/grafana/dev/.env` (copy from [`.env.example`](../../resources/vault/_admin/grafana/dev/.env.example) and set `OTEL_EXPORTER_OTLP_ENDPOINT` + `OTEL_EXPORTER_OTLP_HEADERS` from Grafana Cloud → your stack → OpenTelemetry → Configure).

With `.env` in place:

```bash
docker compose up -d --build
```

- `OTEL_JAVAAGENT_ENABLED=true` in compose turns on the Java agent ([`docker-entrypoint.sh`](app/containers/docker-entrypoint.sh)).
- Service names in Grafana: `kafka-producer-api`, `kafka-producer-scheduler`.
- Metrics export is throttled via `OTEL_METRIC_EXPORT_INTERVAL` in the vault file (default 5 minutes).

To run locally **without** Grafana, set `OTEL_JAVAAGENT_ENABLED: "false"` on api/scheduler in [`compose.yaml`](compose.yaml) or omit/empty the vault `.env` exporter vars.

Verify: call the API, then check traces in Grafana Cloud for those service names.

## Full pipeline (cluster)

```bash
cd scripts
python pipeline_parser.py kafka-producer
```

See [scripts/README.md](../../scripts/README.md).

## Repo-wide Gradle tasks

From `apps/kafka-producer/`:

| Step | Command |
|------|---------|
| Lint (all modules) | `./gradlew check -x test` |
| Test (all modules) | `./gradlew test -x bootJar` *(needs `DATABASE_*` — see API README)* |
| Build JARs | `./gradlew bootJar` |

## End-to-end test (cluster)

After deploy to `dev`:

```bash
minikube kubectl -- port-forward -n dev deployment/kafka-producer-api-dev 8085:8080

curl 'http://localhost:8085/weather/current?city=London'
curl 'http://localhost:8085/message/produce/alice'
```

Scheduler flushes the outbox to `example-topic`; verify in [Kafka UI](../infra/kafka-ui/README.md) or kafka-worker consumer logs.
