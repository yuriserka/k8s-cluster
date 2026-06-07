import unittest

from k8s_cluster.commands.app.drop_service import get_helm_releases


class TestGetHelmReleases(unittest.TestCase):
    def test_kafka_worker_dev_install_steps(self):
        releases = get_helm_releases("kafka-worker", "dev")
        self.assertEqual(
            releases,
            [
                "kafka-worker-api",
                "kafka-worker-example-topic-consumer",
                "kafka-worker-scheduler",
            ],
        )

    def test_kafka_producer_dev_install_steps(self):
        releases = get_helm_releases("kafka-producer", "dev")
        self.assertEqual(releases, ["kafka-producer-api", "kafka-producer-scheduler"])
