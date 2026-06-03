# Migrate container (`kafka-producer-migrate`)

One-shot image that runs Flyway against PostgreSQL via Gradle (`:app:core:flywayMigrate`). Used in the pipeline `dev-migrate` step (in-cluster job), not a long-running service.

Schema and migrations live in [`app/core`](../../core) (`flyway.conf`, `src/main/resources/db/migration`).

**Prerequisites:** JDK **21** for local Gradle runs; Docker for the container image.

---

## Run the container

### Option A — Gradle (local / CI)

From the [kafka-producer](../../../) repo root, with Postgres reachable:

```bash
export DATABASE_USER=root
export DATABASE_PASSWORD=example
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_NAME=kafka-producer

./gradlew :app:core:flywayMigrate -Dflyway.configFiles=flyway.conf
```

Config file path is relative to `app/core` (Gradle project dir).

For pipeline-style test DB (port **5434**):

```bash
export DATABASE_USER=test
export DATABASE_PASSWORD=test
export DATABASE_HOST=localhost
export DATABASE_PORT=5434
export DATABASE_NAME=kafka-producer

./gradlew :app:core:flywayMigrate -Dflyway.configFiles=flyway.conf
```

Cluster migrate uses vault credentials and host `postgresql` — see [`scripts/README.md`](../../../../../scripts/README.md) (`database_migration` step).

### Option B — Docker image

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

On Linux, replace `host.docker.internal` with your host IP or `--network host` if Postgres listens on the host.

### Environment variables

| Variable | Required | Example |
|----------|----------|---------|
| `DATABASE_USER` | yes | `root` |
| `DATABASE_PASSWORD` | yes | `example` |
| `DATABASE_HOST` | yes | `postgresql` (in cluster) |
| `DATABASE_PORT` | yes | `5432` |
| `DATABASE_NAME` | yes | `kafka-producer` |

Substituted into [`app/core/flyway.conf`](../../core/flyway.conf).

### Publish to minikube (pipeline)

```bash
cd scripts
python publish_app.py -r kafka-producer-migrate \
  -d app/containers/migrate/Dockerfile \
  -p ../apps/kafka-producer -n dev -k -t dev
```

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
