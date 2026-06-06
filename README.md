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
helm repo add bitnami https://charts.bitnami.com/bitnami
minikube kubectl -- create namespace dev

helm install kafka bitnami/kafka -n dev -f apps/infra/kafka/values.yaml
helm install kafka-ui kafka-ui/kafka-ui -n dev -f apps/infra/kafka-ui/values.yaml
helm install postgresql bitnami/postgresql -n dev -f apps/infra/postgresql/values.yaml
```

## Local dev with Compose

Run apps on Docker Compose without minikube — see:

- [kafka-producer README](apps/kafka-producer/README.md)
- [kafka-worker README](apps/kafka-worker/README.md)

Both use network **`k8s-cluster-local`** and shared infra containers (`k8s-cluster-postgres`, `k8s-cluster-kafka`, `k8s-cluster-localstack`). Start infra once with the `infra` profile (via each app's `.env`), then start the second app with:

```bash
COMPOSE_PROFILES= docker compose up -d --build --no-deps <services>
```

## Cluster deploy (pipeline)

From `scripts/` (see [scripts/README.md](scripts/README.md)):

```bash
cd scripts
make deploy-app kafka-producer   # or kafka-worker
```

This runs the full `.pipeline`: lint, test, publish images, in-cluster migrate (`create_database.py` + migration job), and Helm deploy. **No port-forward or manual `create_database.py` is required** when using the full pipeline.

Manual equivalent:

```bash
cd scripts
python pipeline_parser.py <app_name>
```

To create a database manually (e.g. before a partial run), `create_database.py` execs into `postgresql-0` in-cluster — no port-forward needed:

```bash
python create_database.py --namespace dev --repository <app_name>
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

```bash
helm uninstall <app_name> -n dev
```

to uninstall every Helm release that app's pipeline deploys (all `kind: install` steps for that repo/namespace):

```bash
cd scripts
python remove_all_pods.py --namespace dev --repository <app_name>
```

and to stop minikube and all services just run:

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