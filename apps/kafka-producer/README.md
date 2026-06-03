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
