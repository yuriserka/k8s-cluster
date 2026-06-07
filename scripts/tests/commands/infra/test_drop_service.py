import unittest

from k8s_cluster.commands.infra.drop_service import resolve_services
from k8s_cluster.commands.infra.types import DropMode, InfraService


class TestResolveServices(unittest.TestCase):
    def test_cluster_default_order(self):
        services = resolve_services(None, DropMode.cluster)
        self.assertEqual(services, ["kafka-ui", "localstack", "kafka", "postgresql"])

    def test_compose_default_order(self):
        services = resolve_services(None, DropMode.compose)
        self.assertEqual(services, ["localstack", "kafka", "postgresql"])

    def test_dedupe_selected_services(self):
        services = resolve_services(
            [InfraService.kafka, InfraService.kafka, InfraService.postgresql],
            DropMode.cluster,
        )
        self.assertEqual(services, ["kafka", "postgresql"])
