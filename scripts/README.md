# Scripts

Python helpers that simulate a CI/CD pipeline locally: build images, run tests (Testcontainers Postgres), migrate databases in the cluster, and deploy apps with Helm.

**Run every command from this directory** (`scripts/`). Paths are resolved via [`k8s_cluster/paths.py`](k8s_cluster/paths.py) (`SCRIPT_DIR` = this folder, `REPO_ROOT` = repository root).

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
make check                             # lint + unit tests
make test                              # unittest discover (tests/ mirrors k8s_cluster/)
make print-repositories                # list deployable repos (excludes infra)
make deploy-app kafka-worker           # install-quiet + full pipeline
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

`deploy-app` runs `install-quiet` then `python -m k8s_cluster pipeline run <repo>`. Available repos match folders under `apps/` except `infra`.

### CLI entry point

All commands are available through a single Typer app:

```bash
python -m k8s_cluster --help
python -m k8s_cluster pipeline run kafka-worker
python -m k8s_cluster infra install --help
python -m k8s_cluster app drop --repository kafka-worker --namespace dev
python -m k8s_cluster database create --namespace dev --repository kafka-worker
```

| Old script | New command |
|------------|-------------|
| `pipeline_parser.py <repo>` | `python -m k8s_cluster pipeline run <repo>` |
| `install_infra.py` | `python -m k8s_cluster infra install` |
| `drop_infra.py` | `python -m k8s_cluster infra drop` |
| `drop_app.py` | `python -m k8s_cluster app drop` |
| `publish_app.py` | `python -m k8s_cluster app publish` |
| `install_app.py` | `python -m k8s_cluster app install` |
| `create_database.py` | `python -m k8s_cluster database create` |

**CLI conventions:** Every subcommand uses [Typer](https://typer.tiangolo.com/). Options use descriptive long names (`--namespace`, `--repository`, …). Run `python -m k8s_cluster <group> --help` for the full list.

For cluster workflows, start infra first:

```bash
make setup-infra
```

Or manually: `python -m k8s_cluster infra install --help`.

## Package layout

```text
scripts/
  Makefile
  code_checks.py
  tests/                    # mirrors k8s_cluster/ layout
  k8s_cluster/
    __main__.py             # sole entry: python -m k8s_cluster
    paths.py
    cli.py
    utils/                  # shell, env_files, docker, compose_runner
    services/               # kubectl, pod_wait, helm
    commands/
      pipeline/             # pipeline run
      infra/                # install, drop
      app/                  # drop, publish, install
      database/             # create
```

| Module | Purpose |
|--------|---------|
| [`commands/infra/`](k8s_cluster/commands/infra/) | Installs/uninstalls shared infra (cluster: Helm; compose: `apps/infra/compose.yaml`) |
| [`commands/app/drop_service.py`](k8s_cluster/commands/app/drop_service.py) | Uninstalls app Helm releases from an app's `.pipeline` install steps |
| [`commands/pipeline/`](k8s_cluster/commands/pipeline/) | Runs an app's full `.pipeline` file (services + steps) |
| [`commands/database/service.py`](k8s_cluster/commands/database/service.py) | Creates a PostgreSQL database in the cluster (PG15+ grants) |
| [`commands/app/publish_service.py`](k8s_cluster/commands/app/publish_service.py) | Builds a Docker image for one application component |
| [`commands/app/install_service.py`](k8s_cluster/commands/app/install_service.py) | Renders Helm values and runs `helm upgrade --install` |
| [`services/pod_wait.py`](k8s_cluster/services/pod_wait.py) | Shared Kubernetes pod wait helpers (state machine polling) |

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

- `infra install` — infra pods after Helm (`make setup-infra`)
- `pipeline run` — `database_migration` one-shot pods and post-`install` rollout pods (matched by `pipeline_id` annotation)

Compose infra waits (`infra install --mode compose`) still use Docker container checks, not this state machine.

## Infra install (`infra install`)

Installs PostgreSQL, Kafka, and LocalStack (Kafka UI is opt-in).

```bash
python -m k8s_cluster infra install                              # cluster (default namespace dev)
python -m k8s_cluster infra install --mode compose               # Docker Compose from apps/infra/
python -m k8s_cluster infra install --with-kafka-ui              # cluster only
make setup-infra                                                 # Makefile wrapper
```

| Option | Default | Description |
|--------|---------|-------------|
| `--mode` | `cluster` | `cluster` or `compose` |
| `--namespace` | `dev` | Kubernetes namespace (cluster mode) |
| `--with-kafka-ui` | off | Install Kafka UI Helm release |

Cluster mode requires minikube + helm. LocalStack auth token is read from `resources/vault/_admin/aws/<namespace>/.env`. App deploy (`make deploy-app`) expects cluster infra to be running first.

## Infra drop (`infra drop`)

Removes infra installed by `infra install`.

```bash
python -m k8s_cluster infra drop                                 # cluster (default namespace dev)
python -m k8s_cluster infra drop --service postgresql            # one service
python -m k8s_cluster infra drop -s kafka -s localstack          # multiple services
python -m k8s_cluster infra drop --mode compose --service kafka
python -m k8s_cluster infra drop --mode compose --volumes -s postgresql
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

## App drop (`app drop`)

Uninstalls every Helm release from `kind: install` steps in `apps/<repo>/.pipeline` for the given namespace.

```bash
python -m k8s_cluster app drop --repository kafka-worker --namespace dev
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
python -m k8s_cluster pipeline run kafka-worker
# or: make deploy-app kafka-worker
```

On success or failure, any containers started from the app's `.pipeline` `services` block are removed, and the temp copy `tmp-<repo>-pipeline/` is deleted.

**Image tags in the pipeline:** publish and install steps use the step `env` value as the Docker/Helm tag (e.g. `env: dev` → `kafka-worker-api-dev:dev`). Each pipeline run overwrites that tag in minikube instead of creating a new timestamp tag per run.

If you see a Docker name conflict from an interrupted run, remove the container manually or re-run the pipeline (it removes leftover containers before `docker run`).

### Cluster database (`database create`)

[`database create`](k8s_cluster/commands/database/service.py) runs **`kubectl exec` into `postgresql-0`** — no port-forward required. The full pipeline calls it automatically inside `database_migration` steps before migrate jobs.

Run manually only when debugging or running a partial workflow:

```bash
python -m k8s_cluster database create --namespace dev --repository kafka-worker
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

These are invoked by `pipeline run` for steps with `kind: publish` or `kind: install`. You can also run them directly.

**Publish** — build image tagged `<repo>-<namespace>:<tag>`:

```bash
python -m k8s_cluster app publish --repository kafka-worker-api --dockerfile Dockerfile \
  --app-path /path/to/build/context --namespace dev --tag dev --use-minikube-docker
```

| Option | Description |
|--------|-------------|
| `--repository` | Image/repository name (e.g. `kafka-worker-api`) |
| `--dockerfile` | Dockerfile path (relative to `--app-path`) |
| `--app-path` | Build context directory |
| `--namespace` | Namespace / environment (e.g. `dev`) |
| `--tag` | Image tag (default: `latest`) |
| `--use-minikube-docker` | Build with `docker build` against minikube's Docker daemon |
| `--build-args` | Optional JSON object of Docker build-args |

### OpenTelemetry instrumentation (`app publish`)

When `instrumentation` is present in `../resources/<application>/<namespace>.yaml`, [`publish_service.py`](k8s_cluster/commands/app/publish_service.py) writes a temp Dockerfile that adds OTel packages and env vars before `docker build`.

Grafana OTLP credentials come from `resources/vault/_admin/grafana/<namespace>/.env`.

**Install** — idempotent Helm deploy (`helm upgrade --install`):

```bash
python -m k8s_cluster app install --repository kafka-worker --application kafka-worker-api \
  --params-file api.yaml --app-path /path/to/app --namespace dev --tag dev
```

Each install writes pod annotations `pipeline_id` and `pipeline_deployed_at` so repeated deploys with the same image tag still roll out new pods. When run via `pipeline run`, all `install` steps in one pipeline run share the same `pipeline_id` and timestamp.

### Inspecting injected env (ConfigMap + Secret)

On `app install`, [`install_service.py`](k8s_cluster/commands/app/install_service.py) builds Helm values from three sources:

| Source | Helm field | Kubernetes object | Examples |
|--------|------------|-------------------|----------|
| `apps/<repo>/kube/<namespace>/*.yaml` `env:` | `env` | ConfigMap `{app}-{ns}-configmap` | `KAFKA_BOOTSTRAP_SERVERS`, platform-injected `ALLOWED_HOSTS` |
| `resources/vault/<repo>/…` + optional `vaultShared` | `secretEnv` | Secret `{app}-{ns}-secret` | `DATABASE_*`, `AWS_*` |
| Rendered snapshot | — | `apps/<repo>/<application>-<namespace>.yaml` | full manifest Helm applied |

Vault files live under `resources/vault/` (see [database create](#cluster-database-database-create) for paths). Infra-only keys (e.g. `LOCALSTACK_AUTH_TOKEN`) stay in the LocalStack container and are **not** mounted into app pods.

Replace `kafka-worker-api` / `dev` with your application and namespace.

**List resource names**

```bash
minikube kubectl -- get configmap,secret -n dev -l app.kubernetes.io/name=kafka-worker-api
```

**ConfigMap (non-secret env)**

```bash
# keys and values (plain text)
minikube kubectl -- get configmap kafka-worker-api-dev-configmap -n dev -o yaml

# single key
minikube kubectl -- get configmap kafka-worker-api-dev-configmap -n dev \
  -o jsonpath='{.data.KAFKA_BOOTSTRAP_SERVERS}{"\n"}'
```

**Secret (credentials)**

```bash
# key names only (values are base64-encoded)
minikube kubectl -- get secret kafka-worker-api-dev-secret -n dev -o jsonpath='{range $k,$v := .data}{printf "%s\n" $k}{end}'

# decode one value (dev debugging only — do not paste output in tickets)
minikube kubectl -- get secret kafka-worker-api-dev-secret -n dev \
  -o jsonpath='{.data.DATABASE_PASSWORD}' | base64 -d; echo
```

**What the running pod actually sees**

Pods load both via `envFrom` (see `envs/dev/templates/deployment.yaml`). To list the merged environment inside the container:

```bash
POD=$(minikube kubectl -- get pods -n dev -l app.kubernetes.io/name=kafka-worker-api \
  -o jsonpath='{.items[0].metadata.name}')

# all env vars (secrets + configmap + image defaults)
minikube kubectl -- exec -n dev "$POD" -- env | sort

# filter to injected keys
minikube kubectl -- exec -n dev "$POD" -- env | sort | grep -E '^(DATABASE_|AWS_|KAFKA_|ALLOWED_HOSTS)'
```

**Which objects are wired in**

```bash
minikube kubectl -- describe pod -n dev "$POD" | sed -n '/Environment:/,/Mounts:/p'
```

Shows `ConfigMap` / `Secret` refs and any inline env vars.

**Compare with local vault before deploy**

```bash
# what install would put in secretEnv (from repo root)
cd scripts && .venv/bin/python -c "
from k8s_cluster.utils.vault import get_secrets_for_app
import json
print(json.dumps(get_secrets_for_app('kafka-worker', 'dev', ['aws']), indent=2))
"
```

### Pipeline log output

`pipeline run` prints a header/footer around each step (`STEP i/N`, kind, key fields, duration, exit code) so output from one step is visually separated from the next. Optional `services:` blocks get a similar `SERVICE i/N` header.

## Pipeline step kinds

Defined in each app's `apps/<repo>/.pipeline`:

| `kind` | Handler behavior |
|--------|------------------|
| *(none)* | Runs shell `cmd` list in the temp pipeline directory |
| *(none)* `test` + minikube docker-env | Prepends `DOCKER_HOST=unix:///var/run/docker.sock` so Testcontainers use Docker Desktop |
| `credentials` | Writes vault secrets to `output_file` |
| `database_migration` | In-cluster migrate via one-shot pod + state-machine wait |
| `publish` | Calls `app publish` with `--tag` set to the step `env` |
| `install` | Calls `app install` then waits for rollout pod with matching `pipeline_id` annotation |

### `database_migration` (in-cluster)

`dev-migrate` runs inside minikube: waits for `postgresql-0` (state machine), runs `database create`, then creates a one-shot migrate pod, waits for `FINISHED` (`phase=Succeeded`), and deletes the pod.

Failed migrate aborts the pipeline before deploy.

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

- **Compose container name already in use** — infra is already running from `apps/infra/`; start apps with `docker compose up -d --build --no-deps <services>`.
- **Docker container name already in use** (pipeline) — `docker rm -f <repo>-<service_name>` or re-run `pipeline run`.
- **`permission denied for schema public`** — run `database create` for that repo/namespace, then migrate again.
- **Pipeline fails on `rsync`** — run from `scripts/` (paths use `REPO_ROOT`).
- **Publish: `lstat /home/...: no such file or directory`** — WSL path passed to Docker Desktop; publish builds via `cd` + relative context. Ensure minikube is running.
- **ErrImageNeverPull** — image tag in Helm must exist in `minikube image ls`; publish must succeed before deploy (pipeline uses tag = `env`, e.g. `:dev`).
