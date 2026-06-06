# Kafka Producer

Gradle multi-module app (Java **21**): **API** (HTTP → outbox), **scheduler** (outbox → Kafka), **migrate** (Flyway). Shared domain and persistence in `app/core`.

## Containers

| Container | README | Role |
|-----------|--------|------|
| API | [app/containers/api/README.md](app/containers/api/README.md) | REST API, outbox writes |
| Scheduler | [app/containers/scheduler/README.md](app/containers/scheduler/README.md) | Publishes outbox to Kafka |
| Migrate | [app/containers/migrate/README.md](app/containers/migrate/README.md) | Flyway migrations (one-shot) |

Each README covers **run** (env vars) and **tests** for that piece. Lint and coverage are project-wide — see [Repo-wide Gradle tasks](#repo-wide-gradle-tasks).

## Quick start (all services locally)

From this directory, with [minikube docker-env](../../README.md#startingstoping) only if you build images for the cluster:

[`compose.yaml`](compose.yaml) is self-contained on network **`k8s-cluster-local`**. Infra (Postgres, Kafka, LocalStack) uses the `infra` profile (enabled via [`.env`](.env)).

**This app only:**

```bash
docker compose up --build
docker compose up -d postgres && make migrate   # required before API/scheduler use
```

**Note:** `docker compose up` does **not** run Flyway automatically — run `make migrate` after Postgres is up.

**Second app while infra is already running** (skip infra to avoid container-name conflicts):

```bash
COMPOSE_PROFILES= docker compose up -d --build --no-deps api scheduler
```

- API: http://localhost:8080  
- Scheduler actuator: http://localhost:8081/actuator/health  
- Postgres: localhost:5432 (database `kafka-producer`)  
- Kafka: localhost:9092  
- LocalStack: localhost:4566  

Create Kafka topic `example-topic` — [Kafka infra README](../infra/kafka/README.md).

## Shared infra with kafka-worker

Both apps share network **`k8s-cluster-local`** and fixed container names (`k8s-cluster-postgres`, `k8s-cluster-kafka`, `k8s-cluster-localstack`). Start infra from either app's compose (`.env` enables the `infra` profile).

If [kafka-worker](../kafka-worker/README.md) started Postgres first, database `kafka-worker` is created via [`initdb/`](../kafka-worker/initdb/) only on **first** volume init. If the volume already existed, create the worker DB manually or re-run worker migrations.

## Grafana / OpenTelemetry

### Compose (local)

Compose loads OTLP credentials and exporter settings from:

`resources/vault/_admin/grafana/dev/.env` (copy from [`.env.example`](../../resources/vault/_admin/grafana/dev/.env.example) and set `OTEL_EXPORTER_OTLP_ENDPOINT` + `OTEL_EXPORTER_OTLP_HEADERS` from Grafana Cloud → your stack → OpenTelemetry → Configure).

With `.env` in place:

```bash
docker compose up -d --build
```

- `OTEL_JAVAAGENT_ENABLED=true` in compose turns on the Java agent ([`docker-entrypoint.sh`](app/containers/docker-entrypoint.sh)).
- Service names in Grafana: `kafka-producer-api`, `kafka-producer-scheduler`.
- `service.namespace=local` in `OTEL_RESOURCE_ATTRIBUTES` ([`Dockerfile.dev`](app/containers/Dockerfile.dev)).
- Metrics export is throttled via `OTEL_METRIC_EXPORT_INTERVAL` in the vault file (default 5 minutes).

To run locally **without** Grafana, set `OTEL_JAVAAGENT_ENABLED: "false"` on api/scheduler in [`compose.yaml`](compose.yaml).

Verify: call the API, then check traces in Grafana Cloud for those service names.

### Cluster (`dev` namespace)

OpenTelemetry is injected at **publish time** by [`publish_app.py`](../../scripts/publish_app.py) when [`resources/kafka-producer-api/dev.yaml`](../../resources/kafka-producer-api/dev.yaml) (and scheduler) define:

```yaml
instrumentation:
  enabled: true
  javaAgent:
    version: "2.15.0"
```

OTLP endpoint/headers come from `resources/vault/_admin/grafana/dev/.env`. `service.namespace=dev` is set in the instrumented Dockerfile. Not configured in `kube/dev/*.yaml` params files.

## Graceful shutdown

- **Spring:** `server.shutdown: graceful` with 30s phase timeout in [`application.yaml`](app/core/src/main/resources/application.yaml).
- **Kubernetes:** `terminationGracePeriodSeconds: 60` in the shared Helm chart ([`envs/dev/values.yaml`](../../envs/dev/values.yaml)).

## Full pipeline (cluster)

```bash
cd scripts
make deploy-app kafka-producer
# or: python pipeline_parser.py kafka-producer
```

See [scripts/README.md](../../scripts/README.md).

## Repo-wide Gradle tasks

From `apps/kafka-producer/`:

| Step | Command |
|------|---------|
| Makefile (all targets) | `make help` |
| Lint + test gate | `make check` |
| Migrate (compose Postgres) | `make migrate` *(start postgres first: `docker compose up -d postgres`)* |
| Lint (Checkstyle + PMD, all modules) | `./gradlew codeChecks` or `make code-checks` |
| Lint (api + core) | `./gradlew :app:containers:api:codeChecks` |
| Lint (scheduler + core) | `./gradlew :app:containers:scheduler:codeChecks` |
| Test (+ JaCoCo report, verification, aggregation) | `./gradlew test -x bootJar` |
| Build JARs | `./gradlew bootJar` |

### Quality reports

After `./gradlew codeChecks`:

| Report | Path |
|--------|------|
| Checkstyle (per module) | `app/<module>/build/reports/checkstyle/` |
| PMD (per module) | `app/<module>/build/reports/pmd/` |

After test + coverage:

| Report | Path |
|--------|------|
| JaCoCo (per module) | `app/<module>/build/reports/jacoco/test/html/index.html` |
| JaCoCo (aggregated) | `build/reports/jacoco/testCodeCoverageReport/html/index.html` |

Minimum line coverage is enforced at **8%** per module (`jacocoTestCoverageVerification`); raise the floor in `app/build.gradle` as tests grow.

### Docker Compose builds

Shared [`Dockerfile.dev`](app/containers/Dockerfile.dev) for api and scheduler — pass `CONTAINER=api` or `CONTAINER=scheduler` (see [`compose.yaml`](compose.yaml)). The build only compiles the **bootJar** and produces a runtime image; no lint or tests during `docker build`. Run `./gradlew codeChecks` and `./gradlew test` on the host (or via CI) when you want those gates.

### Tests (Testcontainers)

Integration tests start a **Postgres container via Testcontainers** ([docs](https://java.testcontainers.org/)) — no external database or `db-credentials` file is required. Docker must be running.

**Docker Engine 29+ (Docker Desktop 4.52+):** Requires Testcontainers **2.x** (pinned via `testcontainersVersion` in `gradle.properties`). Spring Boot 3.3.x would otherwise pull 1.19.x, which fails with `Could not find a valid Docker environment` / HTTP 400 on the Unix socket.

**WSL + Docker Desktop:** If the Unix socket still fails, enable **“Expose daemon on tcp://localhost:2375 without TLS”** in Docker Desktop → Settings → General and set `export DOCKER_HOST=tcp://localhost:2375` ([WSL docs](https://java.testcontainers.org/supported_docker_environment/windows/)).

**Minikube docker-env:** Testcontainers/Ryuk needs Docker Desktop, not minikube’s Docker. [`pipeline_parser.py`](../../scripts/pipeline_parser.py) detects minikube docker-env in the shell and switches to `DOCKER_HOST=unix:///var/run/docker.sock` for the **`test`** step only. For manual `./gradlew test`, unset minikube docker-env or use the same env override.

**Linux CI / native Docker:** Uses the default Unix socket; no extra configuration.

## End-to-end test (cluster)

After deploy to `dev`:

```bash
minikube kubectl -- port-forward -n dev deployment/kafka-producer-api-dev 8085:8080

curl 'http://localhost:8085/weather/current?city=London'
curl 'http://localhost:8085/message/produce/alice'
```

Scheduler flushes the outbox to `example-topic`; verify in [Kafka UI](../infra/kafka-ui/README.md) or kafka-worker consumer logs.
