import os

from k8s_cluster.paths import REPO_ROOT

INFRA_DIR = os.path.join(REPO_ROOT, "apps", "infra")
COMPOSE_DIR = INFRA_DIR
COMPOSE_POSTGRES_CONTAINER = "k8s-cluster-postgres"
COMPOSE_LOCALSTACK_CONTAINER = "k8s-cluster-localstack"

HELM_REPOS = {
    "bitnami": "https://charts.bitnami.com/bitnami",
    "localstack": "https://localstack.github.io/helm-charts",
    "kafka-ui": "https://provectus.github.io/kafka-ui-charts",
}

DEFAULT_CLUSTER_DROP_ORDER = [
    "kafka-ui",
    "localstack",
    "kafka",
    "postgresql",
]

DEFAULT_COMPOSE_DROP_ORDER = [
    "localstack",
    "kafka",
    "postgresql",
]

CLUSTER_HELM_RELEASES = {
    "postgresql": "postgresql",
    "kafka": "kafka",
    "localstack": "localstack",
    "kafka-ui": "kafka-ui",
}

COMPOSE_SERVICES = {
    "postgresql": "postgres",
    "kafka": "kafka",
    "localstack": "localstack",
}
