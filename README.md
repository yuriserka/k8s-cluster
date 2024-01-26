# My k8s cluster

for educational purposes only.

probably everything here could be more optimized but I still dont know a lot

## Starting/Stoping

run the following:

```
minikube [start | stop]
```

## Terminals

for every new terminal you create execute the following

```
eval $(minikube -p minikube docker-env)
```

## Logs

to see the logs for a specific pod do the following:

```
kubectl get pod
kubectl logs -f <POD_NAME>
```

## Port Forwarding

port forward makes possible to interact with pods since they have an internal ip

```
kubectl get pod
kubectl port-forward <POD_NAME> <HOST_PORT_EXPOSED>:<POD_PORT>
```

## Secrets

use the following snipper to inspect the value of some secret

```bash
kubectl get secret

kubectl get secret <SECRET_NAME> -o go-template='{{range $k,$v := .data}}{{printf "%s: " $k}}{{if not $v}}{{$v}}{{else}}{{$v | base64decode}}{{end}}{{"\n"}}{{end}}'
``` 