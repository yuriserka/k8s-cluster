## Kafka-UI

to check the created topics, manage message/consumers, do the following:

### Installing

```
helm install kafka-ui kafka-ui/kafka-ui -n dev -f infra/kafka-ui/values.yaml
```

## Connecting

```
minikube kubectl -- port-forward -n dev kafka-ui-<HASH> 3333:8080
```

open in browser localhost:3333 to access kafka-ui
