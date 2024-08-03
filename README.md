# My k8s cluster

for educational purposes only.

probably everything here could be more optimized but I still dont know a lot

## Starting/Stoping

run the following to get minikube up and running

```bash
minikube start

# note: pick the one below thats works in your terminal
minikube -p minikube docker-env | source
eval (minikube -p minikube docker-env)
```

create the cluster with

```bash
chmod +x ./start-cluster.sh
./start-cluster.sh
```

and to stop just run:

```bash
minikube stop
```

## Reseting everything

to delete all pods/services/statefulsets run:

```bash
kubectl delete all --all --all-namespaces
```

this means that every data you have saved will be lost

## Terminals

for every new terminal you create execute the following

```bash
# note: pick the one below thats works in your terminal
minikube -p minikube docker-env | source
eval (minikube -p minikube docker-env)
```

## Logs

to see the logs for a specific pod do the following:

```bash
kubectl get pod
kubectl logs -f <POD_NAME>
```

## Port Forwarding

port forward makes possible to interact with pods since they have an internal ip

```bash
kubectl get pod
kubectl port-forward <POD_NAME> <HOST_PORT_EXPOSED>:<POD_PORT>
```

## Secrets

use the following snipper to inspect the value of some secret

```bash
kubectl get secret

kubectl get secret <SECRET_NAME> -o go-template='{{range $k,$v := .data}}{{printf "%s: " $k}}{{if not $v}}{{$v}}{{else}}{{$v | base64decode}}{{end}}{{"\n"}}{{end}}'
```

## Alias

put into your shell profile the following alias which is very helpful

```
alias kubectl="minikube kubectl --"
alias k="kubectl"
```