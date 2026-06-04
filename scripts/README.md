# Scripts

Python helpers that simulate a CI/CD pipeline locally: build images, run tests (Testcontainers Postgres), migrate databases in the cluster, and deploy apps with Helm.

**Run every command from this directory** (`scripts/`). Paths are resolved via [`repo_paths.py`](repo_paths.py) (`SCRIPT_DIR` = this folder, `REPO_ROOT` = repository root), so scripts work regardless of the current working directory inside a pipeline temp folder.

## Setup

```bash
cd scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Requirements: Python 3.8+, [Docker](https://docs.docker.com/), [Helm](https://helm.sh/), [minikube](https://minikube.sigs.k8s.io/) (for cluster scripts), and `kubectl` (often via `minikube kubectl --`).

For cluster workflows, start infra from the [project README](../README.md) first.

## Scripts overview

| Script | Purpose |
|--------|---------|
| [`pipeline_parser.py`](pipeline_parser.py) | Runs an app's full `.pipeline` file (services + steps) |
| [`create_database.py`](create_database.py) | Creates a PostgreSQL database in the cluster and grants the app user ownership of the DB and `public` schema (PG15+) |
| [`publish_app.py`](publish_app.py) | Builds a Docker image for one application component |
| [`install_app.py`](install_app.py) | Renders Helm values and installs/upgrades a release in Kubernetes |
| [`remove_all_pods.py`](remove_all_pods.py) | Uninstalls every Helm release declared by `kind: install` steps in an app's `.pipeline` |
| [`repo_paths.py`](repo_paths.py) | Shared `REPO_ROOT`, `SCRIPT_DIR`, and `resolve_path()` used by the scripts above |

## Typical workflow

### Local pipeline (tests, lint, publish, deploy)

Uses the `steps` section in `../apps/<repo>/.pipeline`. **Test steps** start Postgres via Testcontainers in the test process — **kafka-producer** (`./gradlew test`) and **kafka-worker** (`manage.py test`) — so no `.pipeline` `services` block is needed. When minikube docker-env is active in the shell, Testcontainers use Docker Desktop for the **`test`** step (see step kinds below); **publish** steps still build into minikube via `-k`.

```bash
python pipeline_parser.py kafka-worker
```

On success or failure, any containers started from the app's `.pipeline` `services` block are removed, and the temp copy `tmp-<repo>-pipeline/` is deleted.

**Image tags in the pipeline:** publish and install steps use the step `env` value as the Docker/Helm tag (e.g. `env: dev` → `kafka-worker-api-dev:dev`). Each pipeline run overwrites that tag in minikube instead of creating a new timestamp tag per run.

If you see a Docker name conflict from an interrupted run, remove the container manually or re-run the pipeline (it removes leftover containers before `docker run`).

### Cluster database (before migrations against minikube Postgres)

Port-forward Postgres in another terminal:

```bash
kubectl port-forward -n dev service/postgresql 5432:5432
```

Then create the database and apply permissions (safe to re-run):

```bash
python create_database.py -n dev -r kafka-worker
```

Credentials are read from:

- Admin: `resources/vault/_admin/database/<namespace>/.env`
- App: `resources/vault/<repository>/database/<namespace>/.env`

(paths under `REPO_ROOT`)

### Publish and install (usually via pipeline)

These are invoked by `pipeline_parser.py` for steps with `kind: publish` or `kind: install`. You can also run them directly.

**Publish** — build image tagged `<repo>-<namespace>:<tag>`:

```bash
python publish_app.py -r kafka-worker-api -d Dockerfile -p /path/to/build/context -n dev -t dev -k
```

| Flag | Description |
|------|-------------|
| `-r` | Image/repository name (e.g. `kafka-worker-api`) |
| `-d` | Dockerfile path (relative to `-p`) |
| `-p` | Build context directory |
| `-n` | Namespace / environment (e.g. `dev`) |
| `-t` | Image tag (default: `latest`) |
| `-k` | Build with `docker build` against minikube's Docker daemon (`eval "$(minikube docker-env)"`) so images are available with `imagePullPolicy: Never` |

Optional OpenTelemetry instrumentation is applied when enabled in `../resources/<repo>/<namespace>.yaml`.

**Install** — Helm install or upgrade:

```bash
python install_app.py -r kafka-worker -a kafka-worker-api -e api.yaml -p /path/to/app -n dev -t dev
```

| Flag | Description |
|------|-------------|
| `-r` | App repo folder name under `../apps/` (used for vault secrets and chart output path) |
| `-a` | Helm release / application name |
| `-e` | Params file under `kube/<namespace>/` (e.g. `api.yaml`) |
| `-p` | App directory (chart context) |
| `-n` | Kubernetes namespace |
| `-t` | Image tag written into values (default: `latest`) |

Merges, in order: `envs/<namespace>/values.yaml`, app `kube/<namespace>/` overrides, `resources/vault/<repo>/`, and `resources/<application>/<namespace>.yaml` (all under `REPO_ROOT`).

## `pipeline_parser.py` step kinds

Defined in each app's `apps/<repo>/.pipeline`:

| `kind` | Handler behavior |
|--------|------------------|
| *(none)* | Runs shell `cmd` list in the temp pipeline directory |
| *(none)* `test` + minikube docker-env | Same as above; if `MINIKUBE_ACTIVE_DOCKERD` (or minikube `DOCKER_HOST`) is set, the parser prepends `DOCKER_HOST=unix:///var/run/docker.sock` so Testcontainers use Docker Desktop — publish steps still use minikube Docker via `-k` |
| `credentials` | Writes vault secrets to `output_file` (`path` format: `database:<target>:<namespace>`) |
| `database_migration` | In-cluster migrate via `kubectl run` (no port-forward); see below |
| `publish` | Calls `publish_app.py` with `-t` set to the step `env` (same as `-n`) |
| `install` | Calls `install_app.py` with `-t` set to the step `env` |

### Pipeline `services` (optional)

An app's [`.pipeline`](../apps/) file can define an optional top-level **`services:`** block. This is **not** Docker Compose (`compose.yaml`) and **not** a Kubernetes Service — it is a **pipeline-only** mechanism for starting Docker containers before `steps` run.

[`pipeline_parser.py`](pipeline_parser.py) handles each service entry like this:

1. **`docker run -d`** with a fixed container name `{repo}-{service_name}` (e.g. `kafka-worker-pgsql_database`)
2. **Port mapping** from `image_port_map` (host port → container port)
3. **Wait** until Postgres is ready (`pg_isready`), when the image is Postgres
4. **Write env vars** to `output_file` (e.g. `./db-credentials`) from the `env_vars` map — typically `KEY=value` lines for shell `export $(cat ./db-credentials)`
5. Run **`steps`**; later commands read that file or connect to the mapped host port
6. **Remove** all started service containers when the pipeline exits (success or failure)

Example (historical kafka-worker pattern — no longer used; tests now use Testcontainers):

```yaml
services:
  pgsql_database:
    image: postgres:16.3
    image_env_vars:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: kafka-worker
    image_port_map: 5433:5432
    env_vars:
      DATABASE_USER: test
      DATABASE_PASSWORD: test
      DATABASE_HOST: localhost
      DATABASE_NAME: kafka-worker
      DATABASE_PORT: 5433
    output_file: ./db-credentials

steps:
  test:
    cmd:
      - "export $(cat ./db-credentials) && python manage.py test"
```

| Field | Purpose |
|-------|---------|
| `image` | Docker image to run |
| `image_env_vars` | `-e` flags passed to `docker run` (container init) |
| `image_port_map` | `-p` host:container port map |
| `env_vars` | Values written to `output_file` for app/test commands |
| `output_file` | Path under the temp pipeline dir (e.g. `./db-credentials`) |

**When to use `services`:** dependencies that pipeline steps need but that are **not** started inside the test/build process — for example a database before Testcontainers existed, or a broker the tests do not spin up themselves.

**Current apps:** **kafka-producer** and **kafka-worker** do **not** define `services`. Their **test** steps start Postgres via **Testcontainers** inside the test process (Gradle / `manage.py test`), so no shared pipeline container or `db-credentials` file is required. You can still add `services` to a new app if its steps need external Docker deps that Testcontainers does not cover yet.

### `database_migration` (in-cluster)

`dev-migrate` always runs inside minikube: waits for `postgresql-0` to be ready, runs `create_database.py`, then one-off pods with `DATABASE_HOST` from vault `CLUSTER_HOST` (Kubernetes Service DNS, default `postgresql`). Do not use `minikube service` URLs for in-cluster migrate pods.

Publish the migrate image **before** `dev-migrate`:

**kafka-worker** — API image includes Django:

```yaml
dev-publish-api:
  kind: publish
  ...
dev-migrate:
  kind: database_migration
  env: dev
  repository: kafka-worker
  image_repo: kafka-worker-api
  cmd:
    - python manage.py showmigrations
    - python manage.py migrate
```

**kafka-producer** — dedicated Gradle/Flyway image:

```yaml
dev-publish-migrate:
  kind: publish
  repo: kafka-producer-migrate
  dockerfile: app/containers/migrate/Dockerfile
  env: dev
dev-migrate:
  kind: database_migration
  env: dev
  repository: kafka-producer
  image_repo: kafka-producer-migrate
  cmd:
    - ./gradlew :app:core:flywayMigrate -Dflyway.configFiles=flyway.conf
```

Image reference: `{image_repo}-{env}:{env}` (e.g. `kafka-worker-api-dev:dev`). Failed migrate aborts the pipeline before deploy.

## `create_database.py`

```bash
python create_database.py -n <namespace> -r <repository>
```

| Flag | Description |
|------|-------------|
| `-n` | Kubernetes namespace (e.g. `dev`) |
| `-r` | Repository name matching `resources/vault/<repository>/database/` |

Executes `psql` inside the `postgresql-0` pod via `minikube kubectl -- exec`:

1. `CREATE DATABASE ... OWNER <app_user>` (may error if the DB already exists)
2. `ALTER DATABASE` / `GRANT CONNECT` as admin
3. `GRANT` / `ALTER SCHEMA public` connected to the app database

See also [PostgreSQL infra notes](../apps/infra/postgresql/README.md).

## `remove_all_pods.py`

Tears down everything an app's pipeline deploys for a given namespace. Despite the filename, it does **not** delete pods directly — it runs `helm uninstall` for each release listed in `kind: install` steps of `apps/<repository>/.pipeline` where `env` matches `-n` and `repo` matches `-r`.

```bash
python remove_all_pods.py -n dev -r kafka-worker
```

| Flag | Description |
|------|-------------|
| `-n` | Kubernetes namespace (must match the install step `env`, e.g. `dev`) |
| `-r` | App folder name under `apps/` (must match the install step `repo`, e.g. `kafka-worker`) |

For `kafka-worker` with `env: dev`, this uninstalls `kafka-worker-api`, `kafka-worker-example-topic-consumer`, and `kafka-worker-scheduler` (the `application` values from each matching install step). `kafka-producer` uninstalls `kafka-producer-api` and `kafka-producer-scheduler`.

Use this to reset cluster state after a pipeline deploy without uninstalling shared infra (Kafka, PostgreSQL, etc.). To remove a single release instead, use `helm uninstall <application> -n <namespace>`.

## Layout assumptions

```
k8s-cluster/
├── apps/<repo>/          # .pipeline, kube/, Dockerfile
├── envs/<namespace>/     # Helm chart templates
├── resources/
│   ├── vault/            # .env secrets
│   └── <application>/    # per-app Helm resource overrides
└── scripts/              # you are here
```

## Troubleshooting

- **Docker container name already in use** — `docker rm -f <repo>-<service_name>` or re-run `pipeline_parser.py`.
- **`permission denied for schema public`** (Django migrations on cluster) — run `create_database.py` for that repo/namespace, then migrate again.
- **Pipeline fails on `rsync`** — run from `scripts/` (or any cwd; paths use `REPO_ROOT`).
- **Publish: `lstat /home/...: no such file or directory`** — WSL path passed to Docker Desktop; re-run publish after updating `publish_app.py` (builds via `cd` + relative context). Ensure minikube is running.
- **ErrImageNeverPull** — image tag in Helm must exist in `minikube image ls`; publish must succeed before deploy (pipeline uses tag = `env`, e.g. `:dev`).
- **Many old timestamp image tags** — from runs before env-based tagging; remove with `minikube image rm <name:tag>` or prune inside minikube docker (`eval "$(minikube docker-env --shell bash)" && docker image prune`).
