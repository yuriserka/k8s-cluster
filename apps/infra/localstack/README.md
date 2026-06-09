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

**From host (port-forward, cluster):**

```bash
minikube kubectl -- port-forward -n dev svc/localstack 4566:4566
```

Verify from another terminal:

```bash
curl -s http://127.0.0.1:4566/_localstack/health | head -c 200; echo
```

### LocalStack Web App ([app.localstack.cloud](https://app.localstack.cloud/inst/default/resources))

The [LocalStack Web App](https://app.localstack.cloud) (Resource Browser, IAM Policy Stream, etc.) talks to your **local** instance from the browser — traffic stays on your machine ([FAQ](https://docs.localstack.cloud/aws/getting-started/faq/)). It uses `https://localhost.localstack.cloud:4566` by default.

**Requirements**

1. LocalStack running (Compose or cluster + port-forward below).
2. `LOCALSTACK_AUTH_TOKEN` in the instance matches your [LocalStack account token](https://app.localstack.cloud/workspace/auth-tokens) (set in [`resources/vault/_admin/aws/dev/.env`](../../../resources/vault/_admin/aws/dev/.env)).
3. Pro image `localstack/localstack-pro` (see [installation docs](https://docs.localstack.cloud/aws/getting-started/installation/)).

**Chrome / Edge:** lock icon → Site settings → **Local network access** → **Allow** → refresh the Web App ([FAQ](https://docs.localstack.cloud/aws/getting-started/faq/)).

#### Cluster (minikube) — port-forward

Keep one of these running in a terminal.

**Web UI + `awslocal` (port 4566 only):**

```bash
minikube kubectl -- port-forward -n dev svc/localstack 4566:4566
```

**All exported ports** (4566 gateway + 4510–4559 external services — same range as [Compose](../compose.yaml)):

```bash
PORTS=$(minikube kubectl -- get svc localstack -n dev -o jsonpath='{range .spec.ports[*]}{.port}:{.port} ')
minikube kubectl -- port-forward -n dev svc/localstack $PORTS
```

The Helm Service exposes 51 ports (`4566` + `4510`–`4559`). The Web App only needs **4566**; forward the full range if you use external-service bindings (e.g. some Lambda flows).

#### Compose — no port-forward

[`compose.yaml`](../compose.yaml) already binds ports on the host:

- `127.0.0.1:4566:4566`
- `127.0.0.1:4510-4559:4510-4559`

Start LocalStack, then open the Web App:

```bash
cd apps/infra && docker compose up -d localstack
```

#### Troubleshooting Web App connection

| Symptom | Check |
|---------|--------|
| “Could not connect to a licensed LocalStack instance” | Pro image + valid `LOCALSTACK_AUTH_TOKEN` in the running container |
| Pro image warning in logs | Use `localstack/localstack-pro`, not `localstack/localstack` |
| Web App cannot reach instance (Chrome) | Allow **Local network access** for `app.localstack.cloud` |
| `curl` to `127.0.0.1:4566` fails (cluster) | Port-forward not running or wrong namespace |

### Local Compose vs cluster

| | Local Compose | Cluster (`dev`) |
|--|--|--|
| Start | `cd apps/infra && docker compose up -d` or `python -m k8s_cluster infra install --mode compose` | `make setup-infra` |
| Container / service | `k8s-cluster-localstack` on `k8s-cluster-local` | Helm release `localstack` |
| Image | `localstack/localstack-pro:2026.05.2` | `localstack/localstack-pro:2026.05.2` |
| Auth token | `resources/vault/_admin/aws/dev/.env` | Same (injected by install script) |
