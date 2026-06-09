# Infra

Shared infrastructure for local Compose and minikube cluster dev.

## Services

| Service | Cluster (Helm) | Compose | Values / docs |
|---------|----------------|---------|---------------|
| PostgreSQL | `postgresql` | `k8s-cluster-postgres` | [postgresql/](postgresql/) |
| Kafka | `kafka` | `k8s-cluster-kafka` | [kafka/](kafka/) |
| LocalStack | `localstack` | `k8s-cluster-localstack` | [localstack/](localstack/) |
| Kafka UI | optional | — | [kafka-ui/](kafka-ui/) |

Apps connect on network **`k8s-cluster-local`** (Compose) or Kubernetes Service DNS (cluster).

**LocalStack Web App:** browse resources at [app.localstack.cloud](https://app.localstack.cloud/inst/default/resources) — cluster mode needs `port-forward` on `4566`; see [localstack/README.md](localstack/README.md#localstack-web-app-applocalstackcloud).

## Setup

**Cluster (minikube):**

```bash
cd scripts
make setup-infra
```

Installs PostgreSQL, Kafka, and LocalStack in namespace `dev`. Optional: `WITH_KAFKA_UI=1`.

**Compose (Docker):**

```bash
cd apps/infra
docker compose up -d
```

Or: `cd scripts && make setup-infra MODE=compose`

Then start app services from `apps/kafka-producer/` or `apps/kafka-worker/`:

```bash
docker compose up -d --build --no-deps api scheduler
```

## Secrets

| Secret | File |
|--------|------|
| LocalStack auth token | `resources/vault/_admin/aws/dev/.env` |
| Postgres (cluster apps) | `resources/vault/_admin/database/dev/.env` + per-app vault |

See [`k8s_cluster/commands/infra/`](../../scripts/k8s_cluster/commands/infra/) and [scripts/README.md](../../scripts/README.md).

## Teardown

**Cluster:**

```bash
cd scripts
make drop-infra
make drop-infra SERVICES=kafka-ui      # selected release(s) only
```

**Compose:**

```bash
cd scripts
make drop-infra MODE=compose
make drop-infra MODE=compose SERVICES=postgresql
# optional: VOLUMES=1 to remove named volumes for selected service(s)
```
