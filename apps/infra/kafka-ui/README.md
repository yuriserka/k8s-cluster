## Kafka-UI

Use Kafka UI to inspect topics, messages, and consumer groups.

### Installing

Kafka UI is **not** installed by default. Opt in when running infra setup:

```bash
cd scripts
python -m k8s_cluster infra install --with-kafka-ui
# or: make setup-infra WITH_KAFKA_UI=1
```

Manual Helm equivalent:

```bash
helm repo add kafka-ui https://provectus.github.io/kafka-ui-charts
helm upgrade --install kafka-ui kafka-ui/kafka-ui -n dev -f apps/infra/kafka-ui/values.yaml
```

### Connecting

```bash
minikube kubectl -- port-forward -n dev kafka-ui-<HASH> 3333:8080
```

Open http://localhost:3333 in your browser.
