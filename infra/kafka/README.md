## Kafka

### Installing

```
helm install kafka bitnami/kafka -n dev -f infra/kafka/values.yaml
```

### Connecting

once the deployment and the service is up and running, to create a topic, do the following:

```
minikube kubectl -- -n dev exec --stdin --tty kafka-controller-0 -- /bin/bash

kafka-topics.sh --bootstrap-server localhost:9092 --topic <TOPIC-NAME> --create --partitions 1 --replication-factor 1
```

