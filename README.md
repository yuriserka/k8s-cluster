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
helm install kafka bitnami/kafka -n dev -f apps/infra/kafka/values.yaml
helm install kafka-ui kafka-ui/kafka-ui -n dev -f apps/infra/kafka-ui/values.yaml
helm install postgresql bitnami/postgresql -n dev -f apps/infra/postgresql/values.yaml
```

simulate a pipeline with the following commands

```bash
# if your pipeline needs to run a migration, then in a terminal with minikube env vars
kubectl port-forward -n dev service/postgresql 5432:5432

# create a new fresh terminal without sourcing minikube env vars then:
python pipeline_parser.py <app_name>
```

if the app is an API run the following to test:

```bash
kubectl port-forward -n dev deployment/<app_name>-dev <host_port>:<app_exposed_port>

```

if the app is a Kafka consumer, consider to open `kafka-ui`

```bash
kubectl port-forward -n dev deployment/kafka-ui <host_port>:8080
```

to stop a specific app execute:

```bash
helm uninstall <app_name> -n dev
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