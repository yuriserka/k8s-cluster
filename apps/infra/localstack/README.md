## LocalStack

S3-compatible API for local dev. In-cluster URL: `http://localstack:4566` (matches kafka-worker Helm values).

Uses the official [localstack/helm-charts](https://github.com/localstack/helm-charts) chart. Auth token is **not** stored in `values.yaml`; [`k8s_cluster infra install`](../../../scripts/k8s_cluster/commands/infra/install_service.py) reads `LOCALSTACK_AUTH_TOKEN` from [`resources/vault/_admin/aws/dev/.env`](../../../resources/vault/_admin/aws/dev/.env) at install time.

### Installing

From the repository root (recommended):

```bash
cd scripts
make setup-infra
```

Manual equivalent:

```bash
helm repo add localstack https://localstack.github.io/helm-charts
helm upgrade --install localstack localstack/localstack \
  -n dev -f apps/infra/localstack/values.yaml
# plus LOCALSTACK_AUTH_TOKEN from vault — use: python -m k8s_cluster infra install
```

Upgrade after changing values:

```bash
cd scripts
python -m k8s_cluster infra install --namespace dev
```

### Connecting

**In-cluster:** `http://localstack:4566`

**From host (port-forward):**

```bash
minikube kubectl -- port-forward -n dev svc/localstack 4566:4566
```

### Local Compose vs cluster

| | Local Compose | Cluster (`dev`) |
|--|--|--|
| Start | `cd apps/infra && docker compose up -d` or `python -m k8s_cluster infra install --mode compose` | `make setup-infra` |
| Container / service | `k8s-cluster-localstack` on `k8s-cluster-local` | Helm release `localstack` |
| Auth token | `resources/vault/_admin/aws/dev/.env` | Same (injected by install script) |
