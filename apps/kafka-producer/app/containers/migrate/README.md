# Migrate container (`kafka-producer-migrate`)

One-shot image that runs Flyway against PostgreSQL. Used in the pipeline `dev-migrate` step (in-cluster job), not a long-running service.

| Context | Tool | Why |
|---------|------|-----|
| **In-cluster (pipeline)** | [Flyway CLI](https://hub.docker.com/r/flyway/flyway) image | Fast one-shot pod (~seconds); no Gradle bootstrap |
| **Local dev** | `./gradlew :app:core:flywayMigrate` | Uses host Gradle cache; same SQL migrations |

Schema and migrations live in [`app/core`](../../core) (`flyway.conf` for Gradle, `src/main/resources/db/migration` for both).

**Prerequisites:** JDK **21** for local Gradle runs; Docker for the container image.

---

## Run migrations

### Option A — Gradle (local)

From the [kafka-producer](../../../) repo root, with Postgres reachable:

**Docker Compose** ([`compose.yaml`](../../../compose.yaml) uses `ysdcr` / `ysdcr`, db `kafka-producer`, port `5432`):

```bash
docker compose up -d postgres
make migrate
```

Or set env vars manually:

```bash
export DATABASE_USER=ysdcr
export DATABASE_PASSWORD=ysdcr
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_NAME=kafka-producer

./gradlew :app:core:flywayMigrate -Dflyway.configFiles=flyway.conf
```

Config file path is relative to `app/core` (Gradle project dir).

**Cluster / vault** credentials (`root` / `example`, host `postgresql`) — see [`scripts/README.md`](../../../../../scripts/README.md) (`database_migration` step); not used for local compose.

### Option B — Docker image (Flyway CLI)

Build from the [kafka-producer](../../../) repo root:

```bash
docker build -t kafka-producer-migrate:local -f app/containers/migrate/Dockerfile .

docker run --rm \
  -e DATABASE_USER=root \
  -e DATABASE_PASSWORD=example \
  -e DATABASE_HOST=host.docker.internal \
  -e DATABASE_PORT=5432 \
  -e DATABASE_NAME=kafka-producer \
  kafka-producer-migrate:local
```

The entrypoint maps `DATABASE_*` env vars to Flyway settings (parity with [`flyway.conf`](../../core/flyway.conf)).

On Linux, replace `host.docker.internal` with your host IP or `--network host` if Postgres listens on the host.

### Environment variables

| Variable | Required | Example |
|----------|----------|---------|
| `DATABASE_USER` | yes | `root` |
| `DATABASE_PASSWORD` | yes | `example` |
| `DATABASE_HOST` | yes | `postgresql` (in cluster) |
| `DATABASE_PORT` | yes | `5432` |
| `DATABASE_NAME` | yes | `kafka-producer` |

### Publish to minikube (pipeline)

```bash
cd scripts
python publish_app.py --repository kafka-producer-migrate \
  --dockerfile app/containers/migrate/Dockerfile \
  --app-path ../apps/kafka-producer --namespace dev --use-minikube-docker --tag dev
```

Pipeline `dev-migrate` runs `/docker-entrypoint.sh migrate` in-cluster (the Job `command` replaces the image entrypoint, so the script must be invoked explicitly).

---

## Tests (migrate / schema)

There is no `:app:containers:migrate` Gradle module. Schema-related tests run in **core**:

```bash
export DATABASE_USER=test
export DATABASE_PASSWORD=test
export DATABASE_HOST=localhost
export DATABASE_NAME=kafka-producer
export DATABASE_PORT=5434

./gradlew :app:core:test -x bootJar
```

Report: `app/core/build/reports/tests/test/index.html`

---

Lint (Checkstyle + PMD) is a **project-wide** task — run `./gradlew codeChecks` from [`apps/kafka-producer/`](../../../README.md), not per module.
