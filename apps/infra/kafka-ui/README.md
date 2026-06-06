## Kafka-UI

Use Kafka UI to inspect topics, messages, and consumer groups.

### Installing

From the repository root:

```bash
helm install kafka-ui kafka-ui/kafka-ui -n dev -f apps/infra/kafka-ui/values.yaml
```

### Connecting

```bash
minikube kubectl -- port-forward -n dev kafka-ui-<HASH> 3333:8080
```

Open http://localhost:3333 in your browser.
