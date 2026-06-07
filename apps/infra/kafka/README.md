## Kafka

Bitnami chart **32.4.3** (Kafka **4.0.0**, KRaft). Images use `bitnamilegacy/kafka` because versioned tags were removed from `docker.io/bitnami`.

### Installing

Recommended:

```bash
cd scripts
make setup-infra
```

Manual Helm equivalent:

```bash
helm upgrade --install kafka bitnami/kafka -n dev -f apps/infra/kafka/values.yaml
```

Upgrade after changing values:

```bash
helm upgrade kafka bitnami/kafka -n dev -f apps/infra/kafka/values.yaml
```

After changing broker count or RF settings, restart controllers so config is picked up:

```bash
minikube kubectl -- delete pod -n dev -l app.kubernetes.io/component=controller-eligible
```

---

## Replication factor (RF)

**Rule:** replication factor cannot be higher than the number of **brokers** (`controller.replicaCount`), not something you set only on `kafka-topics.sh --create`.

| What you changed | Effect |
|------------------|--------|
| `--replication-factor 3` on `example-topic` | Only that topic — **does not** add brokers |
| `controller.replicaCount: 3` in Helm | Actually runs 3 `kafka-controller-*` pods |
| `overrideConfiguration` offsets RF | Controls **`__consumer_offsets`** (consumer groups) |

| Brokers (`controller.replicaCount`) | RF you can use |
|-------------------------------------|----------------|
| 1 | **1** only (see `values.yaml` — RF=1 overrides enabled) |
| 3 | **1**, **2**, or **3** (remove `overrideConfiguration` for default RF=3) |

**Check broker count** (must match the RF you expect):

```bash
minikube kubectl -- get pods -n dev -l app.kubernetes.io/name=kafka
# 1 pod → need overrideConfiguration RF=1 (current values.yaml)
# 3 pods → can use default RF=3
```

**Stuck logs** with one broker and default RF=3:

```text
Sent auto-creation request for Set(__consumer_offsets) to the active controller.
```

Kafka is retrying forever because RF=3 cannot be satisfied on a single node. Fix: apply `values.yaml` with `overrideConfiguration` (RF=1) and upgrade Helm.

There are two places RF matters: **broker config** (internal topics + defaults) and **per-topic** when you create a topic.

### 1. Broker / internal topics (`__consumer_offsets`, etc.)

Edit [`values.yaml`](values.yaml). Chart **32+** uses `controller.overrideConfiguration` (root `extraConfig` is ignored).

**Single broker (typical minikube dev)** — RF must be 1 or consumer groups will not work:

```yaml
controller:
  replicaCount: 1
  overrideConfiguration:
    offsets.topic.replication.factor: "1"
    transaction.state.log.replication.factor: "1"
    transaction.state.log.min.isr: "1"
```

**Three brokers (Kafka defaults)** — omit `overrideConfiguration`; defaults use RF=3:

```yaml
controller:
  replicaCount: 3
  # no overrideConfiguration → offsets.topic.replication.factor defaults to 3
```

Apply:

```bash
helm upgrade kafka bitnami/kafka -n dev -f apps/infra/kafka/values.yaml
```

Verify internal topic exists (needed for consumer groups):

```bash
minikube kubectl -- exec -n dev kafka-controller-0 -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --list
# expect __consumer_offsets when RF matches broker count
```

### 2. Application topics (e.g. `example-topic`)

RF is set when the topic is **created**, not in `values.yaml` (unless you use chart `provisioning`).

**Create with explicit RF** (must be ≤ broker count):

```bash
minikube kubectl -- exec -n dev kafka-controller-0 -- \
  kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --topic example-topic --partitions 1 --replication-factor 1
```

Use `--replication-factor 3` only if `controller.replicaCount` is **3**.

**Change RF on an existing topic** (Kafka only allows *increasing* replicas):

```bash
# example: grow from 1 → 3 replicas (cluster must have 3 brokers)
minikube kubectl -- exec -n dev kafka-controller-0 -- \
  kafka-topics.sh --bootstrap-server localhost:9092 \
  --alter --topic example-topic --partitions 1 --replication-factor 3
```

Check current RF:

```bash
minikube kubectl -- exec -n dev kafka-controller-0 -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic example-topic
```

---

### Connecting

Once the deployment and the service are up, open a shell in the broker pod:

```bash
minikube kubectl -- exec -n dev -it kafka-controller-0 -- bash
```

Bootstrap address for apps inside the cluster: `kafka:9092`.

Create a topic (match `--replication-factor` to your broker count — see table above):

```bash
kafka-topics.sh --bootstrap-server localhost:9092 \
  --topic <TOPIC-NAME> --create --partitions 1 --replication-factor 1
```
