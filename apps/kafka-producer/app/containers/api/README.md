# API container (`kafka-producer-api`)

Spring Boot HTTP API: writes outbox events (weather lookup, user messages). The scheduler publishes them to Kafka.

**Prerequisites:** JDK **21**, run commands from the [kafka-producer](../../../) repo root (`apps/kafka-producer/`).

For minikube image builds, load Docker into minikube first — see [project README](../../../../../README.md#startingstoping).

---

## Run the container

### Option A — Docker Compose (API + Postgres + Kafka)

Starts dependencies and builds via [`Dockerfile.dev`](Dockerfile.dev):

```bash
docker compose up api --build
```

Uses profile `local` (see [`application-local.yaml`](../../core/src/main/resources/application-local.yaml)): Postgres `postgres:5432`, Kafka `kafka:9092`.

API: `http://localhost:8080`

### Option B — Production-style image (pre-built JAR)

```bash
./gradlew :app:containers:api:bootJar

docker build -t kafka-producer-api:local -f app/containers/api/Dockerfile .
docker run --rm -p 8080:8080 \
  -e SPRING_PROFILE=local \
  --network kafka-producer_default \
  kafka-producer-api:local
```

Use `--network` from the compose network if Postgres/Kafka run in compose; otherwise set env vars for profile `dev` (table below).

### Option C — Cluster (`dev` namespace)

Built and deployed by the pipeline (`dev-publish-api`, `dev-deploy-api`). Port-forward:

```bash
minikube kubectl -- port-forward -n dev deployment/kafka-producer-api-dev 8085:8080
```

### Environment variables

| Variable | Required | Example (cluster `dev`) | Notes |
|----------|----------|------------------------|--------|
| `SPRING_PROFILE` | yes | `dev` / `local` | `local` for compose |
| `DATABASE_HOST` | yes (`dev`) | `postgresql` | Service DNS in cluster |
| `DATABASE_PORT` | yes (`dev`) | `5432` | |
| `DATABASE_NAME` | yes (`dev`) | `kafka-producer` | |
| `DATABASE_USER` | yes (`dev`) | `root` | From vault on deploy |
| `DATABASE_PASSWORD` | yes (`dev`) | *(vault)* | |
| `KAFKA_BOOTSTRAP_SERVERS` | yes (`dev`) | `kafka:9092` | |
| `GEOCODING_URL` | yes (`dev`) | `https://geocoding-api.open-meteo.com` | |
| `OPENMETEO_FORECAST_URL` | yes (`dev`) | `https://api.open-meteo.com/v1/forecast` | |
| `OTEL_JAVAAGENT_ENABLED` | no | `false` | [`Dockerfile.dev`](Dockerfile.dev) only |

Helm overrides: [`kube/dev/api.yaml`](../../../kube/dev/api.yaml).

### Try it

```bash
# Weather report → outbox → Kafka (after scheduler runs)
curl 'http://localhost:8080/weather/current?city=London'

# User message event
curl 'http://localhost:8080/message/produce/alice'

curl http://localhost:8080/actuator/health
```

---

## Tests (this container only)

Uses Spring profile `test` and `DATABASE_*` (same as pipeline Postgres on host port **5434**).

Start test Postgres (or use pipeline `services` once), then:

```bash
# From repo root — example credentials matching .pipeline
export DATABASE_USER=test
export DATABASE_PASSWORD=test
export DATABASE_HOST=localhost
export DATABASE_NAME=kafka-producer
export DATABASE_PORT=5434

./gradlew :app:containers:api:test -x bootJar
```

Report: `app/containers/api/build/reports/tests/test/index.html`

---

## Lint (this container only)

Compiles and runs checks without tests:

```bash
./gradlew :app:containers:api:check -x test
```

Shared code in `:app:core` is on the compile classpath; fix core compile errors if this task fails.
