# Scheduler container (`kafka-producer-scheduler`)

Spring Boot app with `@Scheduled` jobs: reads unprocessed rows from the outbox table and publishes them to Kafka (`ProcessOutboxScheduler`).

No public REST API beyond Actuator on port **8080**.

**Prerequisites:** JDK **21**, run commands from the [kafka-producer](../../../) repo root.

For minikube image builds, see [project README](../../../../../README.md#startingstoping).

---

## Run the container

### Option A — Docker Compose

```bash
docker compose up scheduler --build
```

Profile `local` — same Postgres/Kafka as the API. Actuator: `http://localhost:8081/actuator/health` (host port **8081** → container 8080).

Ensure the **API** (or another writer) has inserted outbox rows; the scheduler polls every 60s.

### Option B — Production-style image

```bash
./gradlew :app:containers:scheduler:bootJar

docker build -t kafka-producer-scheduler:local -f app/containers/scheduler/Dockerfile .
docker run --rm -p 8081:8080 \
  -e SPRING_PROFILE=local \
  --network kafka-producer_default \
  kafka-producer-scheduler:local
```

### Option C — Cluster (`dev`)

Pipeline: `dev-publish-scheduler`, `dev-deploy-scheduler`.

```bash
minikube kubectl -- logs -n dev -f deployment/kafka-producer-scheduler-dev
minikube kubectl -- port-forward -n dev deployment/kafka-producer-scheduler-dev 8081:8080
```

### Environment variables

Same as the API container (scheduler shares [`application.yaml`](../../core/src/main/resources/application.yaml) / profiles).

| Variable | Example (`dev`) |
|----------|-----------------|
| `SPRING_PROFILE` | `dev` |
| `DATABASE_HOST` | `postgresql` |
| `DATABASE_PORT` | `5432` |
| `DATABASE_NAME` | `kafka-producer` |
| `DATABASE_USER` | `root` |
| `DATABASE_PASSWORD` | *(vault)* |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` |
| `GEOCODING_URL` | `https://geocoding-api.open-meteo.com` |
| `OPENMETEO_FORECAST_URL` | `https://api.open-meteo.com/v1/forecast` |
| `OTEL_JAVAAGENT_ENABLED` | `true` in compose; entrypoint skips agent when `false` |
| `OTEL_SERVICE_NAME` | `kafka-producer-scheduler` in compose |

Grafana OTLP: same vault env file as API — [kafka-producer README](../../../README.md#grafana--opentelemetry-compose).

Helm overrides: [`kube/dev/scheduler.yaml`](../../../kube/dev/scheduler.yaml).

---

## Tests (this container only)

```bash
export DATABASE_USER=test
export DATABASE_PASSWORD=test
export DATABASE_HOST=localhost
export DATABASE_NAME=kafka-producer
export DATABASE_PORT=5434

./gradlew :app:containers:scheduler:test -x bootJar
```

Report: `app/containers/scheduler/build/reports/tests/test/index.html`

---

## Lint (this container only)

```bash
./gradlew :app:containers:scheduler:check -x test
```
