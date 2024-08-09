# Kafka

to run do in the following order:

```
kubectl apply -f zookeeper.yaml
kubectl apply -f kafka.yaml
kubectl apply -f admin.yaml
```

which expands to something like:

```
kubectl apply -f zookeeper/configmap.yaml
kubectl apply -f zookeeper/service.yaml
kubectl apply -f zookeeper/statefulset.yaml


kubectl apply -f kafka/configmap.yaml
kubectl apply -f kafka/service.yaml
kubectl apply -f kafka/statefulset.yaml

kubectl apply -f admin/configmap.yaml
kubectl apply -f admin/service.yaml
kubectl apply -f admin/deployment.yaml
```

## Kafka

### Connecting

once the deployment and the service is up and running, to create a topic, do the following:

```
kubectl exec --stdin --tty kafka-0 -- /bin/bash

kafka-topics.sh --bootstrap-server localhost:9092 --topic <TOPIC-NAME> --create --partitions 3 --replication-factor 1
```

## Admin

to check the created topics, manage message/consumers, do the following:

### Connecting

```
kubectl get po | grep "kafka-admin"

kubectl port-forward kafka-admin-<HASH> 9090:8080
```

open in browser localhost:9090 to access kafka-ui
