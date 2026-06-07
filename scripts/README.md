# Scripts

Python helpers that simulate a CI/CD pipeline locally: build images, run tests (Testcontainers Postgres), migrate databases in the cluster, and deploy apps with Helm.

**Run every command from this directory** (`scripts/`). Paths are resolved via [`repo_paths.py`](repo_paths.py) (`SCRIPT_DIR` = this folder, `REPO_ROOT` = repository root), so scripts work regardless of the current working directory inside a pipeline temp folder.

## Setup

```bash
cd scripts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements_dev.txt
```

Requirements: Python 3.8+, [Docker](https://docs.docker.com/), [Helm](https://helm.sh/), [minikube](https://minikube.sigs.k8s.io/) (for cluster scripts), and `kubectl` (often via `minikube kubectl --`).

### Makefile

From `scripts/`:

```bash
make help                              # list targets and available app repos
make install                           # pip install requirements + dev deps
make lint                              # black --check + flake8
make format                            # apply black
make check                             # alias for lint
make print-repositories                # list deployable repos (excludes infra)
make deploy-app kafka-worker           # install-quiet + full pipeline_parser.py
make deploy-app kafka-producer
make setup-infra                       # cluster infra (PG + Kafka + LocalStack)
make setup-infra MODE=compose          # Docker Compose infra from apps/infra/
make setup-infra WITH_KAFKA_UI=1       # also install Kafka UI (cluster)
make drop-app kafka-worker             # uninstall app Helm releases
make drop-infra                        # uninstall infra Helm releases (cluster)
make drop-infra MODE=compose           # docker compose down (keep volumes)
make drop-infra MODE=compose VOLUMES=1 # docker compose down -v
make drop-infra SERVICES=postgresql    # drop selected infra only
make drop-infra SERVICES="kafka localstack"
```

`deploy-app` runs `install-quiet` then `pipeline_parser.py <repo>`. Available repos match folders under `apps/` except `infra`.

**CLI conventions:** Every script uses [Typer](https://typer.tiangolo.com/). Options use descriptive long names (`--namespace`, `--repository`, …). Run `python <script>.py --help` for the full list.

For cluster workflows, start infra first:

```bash
make setup-infra
```

Or manually: `python install_infra.py --help`.

## Scripts overview

| Script | Purpose |
|--------|---------|
| [`install_infra.py`](install_infra.py) | Installs shared infra (cluster: Helm; compose: `apps/infra/compose.yaml`) |
| [`drop_infra.py`](drop_infra.py) | Uninstalls shared infra (cluster: Helm; compose: `docker compose down`) |
| [`drop_app.py`](drop_app.py) | Uninstalls app Helm releases from an app's `.pipeline` install steps |
| [`pipeline_parser.py`](pipeline_parser.py) | Runs an app's full `.pipeline` file (services + steps) |
| [`create_database.py`](create_database.py) | Creates a PostgreSQL database in the cluster and grants the app user ownership of the DB and `public` schema (PG15+) |
| [`publish_app.py`](publish_app.py) | Builds a Docker image for one application component |
| [`install_app.py`](install_app.py) | Renders Helm values and runs `helm upgrade --install`; stamps pods with pipeline metadata |
| [`repo_paths.py`](repo_paths.py) | Shared `REPO_ROOT`, `SCRIPT_DIR`, and `resolve_path()` used by the scripts above |
| [`infra_common.py`](infra_common.py) | Shared Kubernetes pod wait helpers (state machine polling) |

## Pod wait state machine

Cluster scripts poll pod status every **5 seconds** (default timeout **120s**) and print lifecycle lines:

```text
postgresql-0: PENDING
postgresql-0: STARTED
postgresql-0: PROGRESSING
postgresql-0: FINISHED
```

States: `PENDING` → `STARTED` → `PROGRESSING` (re-echoed every 5s while not ready) → `FINISHED`. On error or timeout: `FAILED`, followed by a warning with `kubectl get` / `describe` commands for the pod.

Used by:

- [`install_infra.py`](install_infra.py) — infra pods after Helm (`make setup-infra`)
- [`pipeline_parser.py`](pipeline_parser.py) — `database_migration` one-shot pods and post-`install` rollout pods (matched by `pipeline_id` annotation)

Compose infra waits (`install_infra.py --mode compose`) still use Docker container checks, not this state machine.

## `install_infra.py`

Installs PostgreSQL, Kafka, and LocalStack (Kafka UI is opt-in).

```bash
python install_infra.py                              # cluster (default namespace dev)
python install_infra.py --mode compose               # Docker Compose from apps/infra/
python install_infra.py --with-kafka-ui              # cluster only
make setup-infra                                     # Makefile wrapper
```

| Option | Default | Description |
|--------|---------|-------------|
| `--mode` | `cluster` | `cluster` or `compose` |
| `--namespace` | `dev` | Kubernetes namespace (cluster mode) |
| `--with-kafka-ui` | off | Install Kafka UI Helm release |

Cluster mode requires minikube + helm. LocalStack auth token is read from `resources/vault/_admin/aws/<namespace>/.env`. App deploy (`make deploy-app`) expects cluster infra to be running first.

## `drop_infra.py`

Removes infra installed by [`install_infra.py`](install_infra.py).

```bash
python drop_infra.py                                 # cluster (default namespace dev)
python drop_infra.py --service postgresql            # one service
python drop_infra.py -s kafka -s localstack          # multiple services
python drop_infra.py --mode compose --service kafka
python drop_infra.py --mode compose --volumes -s postgresql
make drop-infra
make drop-infra SERVICES=postgresql
```

| Option | Default | Description |
|--------|---------|-------------|
| `--mode` | `cluster` | `cluster` or `compose` |
| `--namespace` | `dev` | Kubernetes namespace (cluster mode) |
| `--volumes` | off | Compose mode: remove volumes for selected service(s) |
| `--service` / `-s` | all | `postgresql`, `kafka`, `localstack`, `kafka-ui` (cluster only for kafka-ui) |

Cluster mode runs `helm uninstall` for each selected release (`--ignore-not-found`). Default order when dropping all: `kafka-ui`, `localstack`, `kafka`, `postgresql`. Drop apps first (`make drop-app`) before infra.

## `drop_app.py`

Uninstalls every Helm release from `kind: install` steps in `apps/<repo>/.pipeline` for the given namespace.

```bash
python drop_app.py --repository kafka-worker --namespace dev
make drop-app kafka-worker
```

| Option | Default | Description |
|--------|---------|-------------|
| `--repository` | required | App folder under `apps/` |
| `--namespace` | `dev` | Kubernetes namespace |

For `kafka-worker` with `env: dev`, this uninstalls `kafka-worker-api`, `kafka-worker-example-topic-consumer`, and `kafka-worker-scheduler`. `kafka-producer` uninstalls `kafka-producer-api` and `kafka-producer-scheduler`. Use this to reset cluster state after a pipeline deploy without uninstalling shared infra; run `make drop-infra` after dropping apps to remove infra too.

## Typical workflow

### Local pipeline (tests, lint, publish, deploy)

Uses the `steps` section in `../apps/<repo>/.pipeline`. **Test steps** start Postgres via Testcontainers in the test process — **kafka-producer** (`./gradlew test`) and **kafka-worker** (`manage.py test`) — so no `.pipeline` `services` block is needed. When minikube docker-env is active in the shell, Testcontainers use Docker Desktop for the **`test`** step (see step kinds below); **publish** steps still build into minikube via `--use-minikube-docker`.

```bash
python pipeline_parser.py kafka-worker
```

On success or failure, any containers started from the app's `.pipeline` `services` block are removed, and the temp copy `tmp-<repo>-pipeline/` is deleted.

**Image tags in the pipeline:** publish and install steps use the step `env` value as the Docker/Helm tag (e.g. `env: dev` → `kafka-worker-api-dev:dev`). Each pipeline run overwrites that tag in minikube instead of creating a new timestamp tag per run.

If you see a Docker name conflict from an interrupted run, remove the container manually or re-run the pipeline (it removes leftover containers before `docker run`).

### Cluster database (`create_database.py`)

[`create_database.py`](create_database.py) runs **`kubectl exec` into `postgresql-0`** — no port-forward required. The full pipeline calls it automatically inside `database_migration` steps before migrate jobs.

Run manually only when debugging or running a partial workflow:

```bash
python create_database.py --namespace dev --repository kafka-worker
```

Creates the database and grants the app user ownership of the DB and `public` schema (required on PostgreSQL 15+). Safe to re-run.

Credentials are read from:

- Admin: `resources/vault/_admin/database/<namespace>/.env`
- App: `resources/vault/<repository>/database/<namespace>/.env`

(paths under `REPO_ROOT`)

**Optional port-forward** — only if you want host-side `psql` or a GUI against cluster Postgres:

```bash
kubectl port-forward -n dev service/postgresql 5432:5432
```

### Publish and install (usually via pipeline)

These are invoked by `pipeline_parser.py` for steps with `kind: publish` or `kind: install`. You can also run them directly.

**Publish** — build image tagged `<repo>-<namespace>:<tag>`:

```bash
python publish_app.py --repository kafka-worker-api --dockerfile Dockerfile \
  --app-path /path/to/build/context --namespace dev --tag dev --use-minikube-docker
```

| Option | Description |
|--------|-------------|
| `--repository` | Image/repository name (e.g. `kafka-worker-api`) |
| `--dockerfile` | Dockerfile path (relative to `--app-path`) |
| `--app-path` | Build context directory |
| `--namespace` | Namespace / environment (e.g. `dev`) |
| `--tag` | Image tag (default: `latest`) |
| `--use-minikube-docker` | Build with `docker build` against minikube's Docker daemon (`eval "$(minikube docker-env)"`) so images are available with `imagePullPolicy: Never` |
| `--build-args` | Optional JSON object of Docker build-args (e.g. `'{"CONTAINER":"api"}'`) |

### OpenTelemetry instrumentation (`publish_app.py`)

When `instrumentation` is present in `../resources/<application>/<namespace>.yaml`, [`publish_app.py`](publish_app.py) writes a temp Dockerfile that adds OTel packages and env vars before `docker build`.

Grafana OTLP credentials come from `resources/vault/_admin/grafana/<namespace>/.env`.

**Java** (`kafka-producer-api`, `kafka-producer-scheduler`):

```yaml
instrumentation:
  enabled: true
  javaAgent:
    version: "2.15.0"
```

Downloads `opentelemetry-javaagent.jar`, injects OTLP `ENV` lines, and prepends `-javaagent` to the image `CMD`.

**Python** (`kafka-worker-*`):

```yaml
instrumentation:
  enabled: true
  pythonAgent:
    version: "0.63b1"
```

Pins `opentelemetry-distro=={version}`, installs `opentelemetry-exporter-otlp`, runs `opentelemetry-bootstrap --action=install`, and injects OTLP `ENV` before `ENTRYPOINT`. Runtime wrapping uses `/docker-entrypoint.sh` → `opentelemetry-instrument` when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.

When `enabled: false`, packages may still be installed but OTLP endpoint env is omitted (entrypoint no-ops without endpoint).

**Install** — idempotent Helm deploy (`helm upgrade --install`):

```bash
python install_app.py --repository kafka-worker --application kafka-worker-api \
  --params-file api.yaml --app-path /path/to/app --namespace dev --tag dev
```

| Option | Description |
|--------|-------------|
| `--repository` | App repo folder name under `../apps/` (used for vault secrets and chart output path) |
| `--application` | Helm release / application name |
| `--params-file` | Params file under `kube/<namespace>/` (e.g. `api.yaml`) |
| `--app-path` | App directory (chart context) |
| `--namespace` | Kubernetes namespace |
| `--tag` | Image tag written into values (default: `latest`) |
| `--pipeline-id` | UUID for this deploy (optional; auto-generated if omitted) |
| `--pipeline-started-at` | ISO-8601 UTC timestamp (optional; auto-generated if omitted) |

Merges, in order: `envs/<namespace>/values.yaml`, app `kube/<namespace>/` overrides, `resources/vault/<repo>/`, and `resources/<application>/<namespace>.yaml` (all under `REPO_ROOT`).

Each install writes pod annotations `pipeline_id` and `pipeline_deployed_at` so repeated deploys with the same image tag still roll out new pods. When run via [`pipeline_parser.py`](pipeline_parser.py), all `install` steps in one pipeline run share the same `pipeline_id` and timestamp.

Inspect on a running pod:

```bash
minikube kubectl -- get pod -n dev -l app.kubernetes.io/instance=kafka-worker-api -o yaml | grep pipeline_
```

## `pipeline_parser.py` step kinds

Defined in each app's `apps/<repo>/.pipeline`:

| `kind` | Handler behavior |
|--------|------------------|
| *(none)* | Runs shell `cmd` list in the temp pipeline directory |
| *(none)* `test` + minikube docker-env | Same as above; if `MINIKUBE_ACTIVE_DOCKERD` (or minikube `DOCKER_HOST`) is set, the parser prepends `DOCKER_HOST=unix:///var/run/docker.sock` so Testcontainers use Docker Desktop — publish steps still use minikube Docker via `--use-minikube-docker` |
| `credentials` | Writes vault secrets to `output_file` (`path` format: `database:<target>:<namespace>`) |
| `database_migration` | In-cluster migrate via one-shot pod + state-machine wait; see below |
| `publish` | Calls `publish_app.main()` with `--tag` set to the step `env` (same as `--namespace`) |
| `install` | Calls `install_app.install_app()` then waits for rollout pod with matching `pipeline_id` annotation |

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

`dev-migrate` runs inside minikube: waits for `postgresql-0` (state machine), runs `create_database.py`, then creates a one-shot migrate pod, waits for `FINISHED` (`phase=Succeeded`), and deletes the pod.

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

**kafka-producer** — Flyway CLI image (see [migrate README](../apps/kafka-producer/app/containers/migrate/README.md)):

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
    - /docker-entrypoint.sh migrate
```

Image reference: `{image_repo}-{env}:{env}` (e.g. `kafka-worker-api-dev:dev`). Failed migrate aborts the pipeline before deploy.

## `create_database.py`

```bash
python create_database.py --namespace <namespace> --repository <repository>
```

| Option | Description |
|--------|-------------|
| `--namespace` | Kubernetes namespace (e.g. `dev`) |
| `--repository` | Repository name matching `resources/vault/<repository>/database/` |

Executes `psql` inside the `postgresql-0` pod via `minikube kubectl -- exec`:

1. `CREATE DATABASE ... OWNER <app_user>` (may error if the DB already exists)
2. `ALTER DATABASE` / `GRANT CONNECT` as admin
3. `GRANT` / `ALTER SCHEMA public` connected to the app database

See also [PostgreSQL infra notes](../apps/infra/postgresql/README.md).

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

- **Compose container name already in use** (`k8s-cluster-kafka`, etc.) — infra is already running from `apps/infra/`; start apps with `docker compose up -d --build --no-deps <services>` (see app READMEs).
- **Docker container name already in use** (pipeline) — `docker rm -f <repo>-<service_name>` or re-run `pipeline_parser.py`.
- **`permission denied for schema public`** (Django migrations on cluster) — run `create_database.py` for that repo/namespace, then migrate again.
- **Pipeline fails on `rsync`** — run from `scripts/` (or any cwd; paths use `REPO_ROOT`).
- **Publish: `lstat /home/...: no such file or directory`** — WSL path passed to Docker Desktop; re-run publish after updating `publish_app.py` (builds via `cd` + relative context). Ensure minikube is running.
- **ErrImageNeverPull** — image tag in Helm must exist in `minikube image ls`; publish must succeed before deploy (pipeline uses tag = `env`, e.g. `:dev`).
- **Many old timestamp image tags** — from runs before env-based tagging; remove with `minikube image rm <name:tag>` or prune inside minikube docker (`eval "$(minikube docker-env --shell bash)" && docker image prune`).
