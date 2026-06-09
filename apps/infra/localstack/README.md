## LocalStack

S3-compatible API for local dev. In-cluster URL: `http://localstack:4566` (matches kafka-worker Helm values).

Uses the official [localstack/helm-charts](https://github.com/localstack/helm-charts) chart with the **Pro** image `localstack/localstack-pro:2026.05.2` (pinned in [`values.yaml`](values.yaml) and [`compose.yaml`](../compose.yaml)). A Pro auth token is required — set `LOCALSTACK_AUTH_TOKEN` in [`resources/vault/_admin/aws/dev/.env`](../../../resources/vault/_admin/aws/dev/.env). The token is **not** stored in `values.yaml`; [`k8s_cluster infra install`](../../../scripts/k8s_cluster/commands/infra/install_service.py) injects it at install time.

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

### Security note (dev only)

[`values.yaml`](values.yaml) mounts the host **`/var/run/docker.sock`** into the LocalStack pod so the chart can spawn Lambda-style sidecars locally. This is convenient on minikube but **must not be copied to production** — it grants the pod broad access to the node Docker daemon. For production, use a LocalStack deployment model that does not require host socket access.

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
| Image | `localstack/localstack-pro:2026.05.2` | `localstack/localstack-pro:2026.05.2` |
| Auth token | `resources/vault/_admin/aws/dev/.env` | Same (injected by install script) |
