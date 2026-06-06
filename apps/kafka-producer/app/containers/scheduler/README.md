# Scheduler container (`kafka-producer-scheduler`)

Spring Boot app with `@Scheduled` jobs: reads unprocessed rows from the outbox table and publishes them to Kafka (`ProcessOutboxScheduler`).

No public REST API beyond Actuator on port **8080**.

**Prerequisites:** JDK **21**, run commands from the [kafka-producer](../../../) repo root.

For minikube image builds, see [project README](../../../../../README.md#startingstoping).

---

## Run the container

### Option A — Docker Compose

Build via shared [`Dockerfile.dev`](../Dockerfile.dev) with `CONTAINER=scheduler` (bootJar only — no lint/tests in the image build). Run `./gradlew :app:containers:scheduler:codeChecks` and `./gradlew test` on the host when you want CI gates — see [kafka-producer README](../../../README.md#repo-wide-gradle-tasks).

```bash
docker compose up -d postgres && make migrate
docker compose up scheduler --build
```

If infra is already running, use `COMPOSE_PROFILES= docker compose up -d --build --no-deps scheduler`.

Profile `local` — same Postgres/Kafka as the API. Actuator: `http://localhost:8081/actuator/health` (host port **8081** → container 8080).

Ensure the **API** (or another writer) has inserted outbox rows; the scheduler polls every 60s.

### Option B — Production-style image

Production [`Dockerfile`](../Dockerfile) has no entrypoint/javaagent unless built via `publish_app` with `javaAgent`. Raw local build:

```bash
./gradlew :app:containers:scheduler:bootJar

docker build -t kafka-producer-scheduler:local -f app/containers/Dockerfile --build-arg CONTAINER=scheduler .
docker run --rm -p 8081:8080 \
  -e SPRING_PROFILE=local \
  --network k8s-cluster-local \
  kafka-producer-scheduler:local
```

### Option C — Cluster (`dev`)

Pipeline: `dev-publish-scheduler`, `dev-deploy-scheduler`. OTel injected at publish; graceful shutdown via Spring + 60s termination grace.

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
| `GEOCODING_URL` | `https://geocoding-api.open-meteo.com` (shared config; scheduler does not call geocoding) |
| `OPENMETEO_FORECAST_URL` | `https://api.open-meteo.com/v1/forecast` (shared config) |
| `OTEL_JAVAAGENT_ENABLED` | `true` in compose; entrypoint skips agent when `false` |
| `OTEL_SERVICE_NAME` | `kafka-producer-scheduler` in compose |
| `OTEL_RESOURCE_ATTRIBUTES` | `service.name=kafka-producer-scheduler,...` in [`Dockerfile.dev`](../Dockerfile.dev) with `CONTAINER=scheduler` |

Grafana OTLP: same vault env file as API — [kafka-producer README](../../../README.md#grafana--opentelemetry).

Helm overrides: [`kube/dev/scheduler.yaml`](../../../kube/dev/scheduler.yaml).

---

## Tests (this container only)

Uses **Testcontainers Postgres** — Docker required. See [kafka-producer README](../../../README.md#tests-testcontainers).

```bash
./gradlew :app:containers:scheduler:test -x bootJar
```

Report: `app/containers/scheduler/build/reports/tests/test/index.html`

---

Lint (Checkstyle + PMD) for this container plus shared `core` code:

```bash
./gradlew :app:containers:scheduler:codeChecks
```

Project-wide lint (all modules): `./gradlew codeChecks` — see [kafka-producer README](../../../README.md#repo-wide-gradle-tasks).
