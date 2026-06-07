# API container (`kafka-producer-api`)

Spring Boot HTTP API: writes outbox events (weather lookup, user messages). The scheduler publishes them to Kafka.

**Prerequisites:** JDK **21**, run commands from the [kafka-producer](../../../) repo root (`apps/kafka-producer/`).

For minikube image builds, load Docker into minikube first — see [project README](../../../../../README.md#startingstoping).

---

## Run the container

### Option A — Docker Compose (API + Postgres + Kafka)

Starts dependencies and builds via shared [`Dockerfile.dev`](../Dockerfile.dev) with `CONTAINER=api` (bootJar only — no lint/tests in the image build). Run `./gradlew :app:containers:api:codeChecks` and `./gradlew test` on the host when you want CI gates — see [kafka-producer README](../../../README.md#repo-wide-gradle-tasks).

```bash
cd ../../../../infra && docker compose up -d
cd ../kafka-producer
make migrate
docker compose up api --build
```

If infra is already running, use `docker compose up -d --build --no-deps api` instead.

Uses profile `local` (see [`application-local.yaml`](../../core/src/main/resources/application-local.yaml)): Postgres `postgres:5432`, Kafka `kafka:9092`.

API: `http://localhost:8080`

### Option B — Production-style image (pre-built JAR)

Production [`Dockerfile`](../Dockerfile) has **no** `docker-entrypoint.sh` or javaagent unless the image was built via [`publish_app.py`](../../../../../scripts/publish_app.py) with `javaAgent` in resources. For a raw local build:

```bash
./gradlew :app:containers:api:bootJar

docker build -t kafka-producer-api:local -f app/containers/Dockerfile --build-arg CONTAINER=api .
docker run --rm -p 8080:8080 \
  -e SPRING_PROFILE=local \
  --network k8s-cluster-local \
  kafka-producer-api:local
```

Connect to compose infra on network **`k8s-cluster-local`**; otherwise set env vars for profile `dev` (table below).

### Option C — Cluster (`dev` namespace)

Built and deployed by the pipeline (`dev-publish-api`, `dev-deploy-api`). OTel javaagent and OTLP env are baked at publish from [`resources/kafka-producer-api/dev.yaml`](../../../../../resources/kafka-producer-api/dev.yaml). Graceful shutdown: Spring lifecycle + 60s pod termination grace.

Port-forward:

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
| `OTEL_JAVAAGENT_ENABLED` | no | `true` (compose) / `false` (image default) | [`docker-entrypoint.sh`](../docker-entrypoint.sh): `false` skips `-javaagent` |
| `OTEL_SERVICE_NAME` | no | `kafka-producer-api` | Set in compose |
| `OTEL_RESOURCE_ATTRIBUTES` | no | `service.name=kafka-producer-api,...` | [`Dockerfile.dev`](../Dockerfile.dev) with `CONTAINER=api`; aligns with `OTEL_SERVICE_NAME` |
| `OTEL_EXPORTER_OTLP_*` | for Grafana | from vault `.env` | See [kafka-producer README](../../../README.md#grafana--opentelemetry) |

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

Uses Spring profile `test` with **Testcontainers Postgres** (no external database). Docker must be running — see [kafka-producer README](../../../README.md#tests-testcontainers) for WSL/Docker Desktop setup.

```bash
./gradlew :app:containers:api:test -x bootJar
```

Report: `app/containers/api/build/reports/tests/test/index.html`

---

Lint (Checkstyle + PMD) for this container plus shared `core` code:

```bash
./gradlew :app:containers:api:codeChecks
```

Project-wide lint (all modules): `./gradlew codeChecks` — see [kafka-producer README](../../../README.md#repo-wide-gradle-tasks).
