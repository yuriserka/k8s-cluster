# My k8s cluster

for educational purposes only.

probably everything here could be more optimized but I still dont know a lot

## Starting/Stoping

run the following to get minikube up and running

```bash
minikube start
```

for every new terminal you create execute the following

```bash
# note: pick the one below thats works in your terminal
minikube -p minikube docker-env | source
eval (minikube -p minikube docker-env)
```

create the infra you need with

```bash
cd scripts
make setup-infra
```

Optional: `make setup-infra WITH_KAFKA_UI=1` for Kafka UI.

## Local dev with Compose

Run apps on Docker Compose without minikube — see:

- [infra README](apps/infra/README.md) — start shared Postgres, Kafka, LocalStack once
- [kafka-producer README](apps/kafka-producer/README.md)
- [kafka-worker README](apps/kafka-worker/README.md)

Both apps use network **`k8s-cluster-local`** and shared infra containers (`k8s-cluster-postgres`, `k8s-cluster-kafka`, `k8s-cluster-localstack`). Start infra from [`apps/infra/`](apps/infra/), then start app services:

```bash
cd apps/infra && docker compose up -d
# or: cd scripts && make setup-infra MODE=compose

cd apps/kafka-producer   # or kafka-worker
docker compose up -d --build --no-deps <services>
```

## Cluster deploy (pipeline)

From `scripts/` (see [scripts/README.md](scripts/README.md)):

```bash
cd scripts
make deploy-app kafka-producer   # or kafka-worker
```

This runs the full `.pipeline`: lint, test, publish images, in-cluster migrate (`database create` + migration job), and Helm deploy. **No port-forward or manual `database create` is required** when using the full pipeline.

Manual equivalent:

```bash
cd scripts
python -m k8s_cluster pipeline run <app_name>
```

To create a database manually (e.g. before a partial run), `database create` execs into `postgresql-0` in-cluster — no port-forward needed:

```bash
python -m k8s_cluster database create --namespace dev --repository <app_name>
```

## Testing deployed apps

Port-forward is only needed to reach cluster services from your host (API curls, Kafka UI):

```bash
kubectl port-forward -n dev deployment/<app_name>-dev <host_port>:<app_exposed_port>
```

For Kafka UI:

```bash
kubectl port-forward -n dev deployment/kafka-ui <host_port>:8080
```

## Stopping apps

Drop app Helm releases (all `kind: install` steps for that repo/namespace):

```bash
cd scripts
make drop-app kafka-worker   # or kafka-producer
```

Or: `python -m k8s_cluster app drop --repository <app_name> --namespace dev`

Drop shared infra (after apps):

```bash
cd scripts
make drop-infra                        # cluster Helm releases
make drop-infra MODE=compose           # compose down (keep volumes)
make drop-infra MODE=compose VOLUMES=1 # compose down -v (all services)
make drop-infra SERVICES=postgresql    # drop selected infra only
```

To stop minikube entirely:

```bash
minikube stop
```

## Logs

you can install [k9s](https://k9scli.io/) which is way more easy or use:

```bash
kubectl logs -n dev -f deployment/<app_name>-dev
```

## Alias

put into your shell profile the following alias which is very helpful

```
alias kubectl="minikube kubectl --"
alias k="kubectl"
```