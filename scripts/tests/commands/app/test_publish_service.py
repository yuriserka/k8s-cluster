import os
import unittest
from concurrent.futures import ThreadPoolExecutor

from k8s_cluster.commands.app.publish_service import add_otel_to_python_dockerfile
from k8s_cluster.paths import REPO_ROOT


class TestParallelPublishInstrumentation(unittest.TestCase):
    def test_parallel_python_instrumentation_isolated(self):
        dockerfile_path = os.path.join(
            REPO_ROOT,
            "apps",
            "kafka-worker",
            "kafkaworker",
            "containers",
            "Dockerfile",
        )
        repositories = [
            "kafka-worker-api",
            "kafka-worker-scheduler",
            "kafka-worker-example-topic-consumer",
        ]
        grafana_secrets = {
            "OTEL_EXPORTER_OTLP_ENDPOINT": "https://example.test/otlp",
            "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
            "OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Basic test",
        }

        def instrument(repository: str) -> str:
            return add_otel_to_python_dockerfile(
                dockerfile_path,
                "0.63b1",
                repository,
                True,
                "dev",
                grafana_secrets,
            )

        created_paths: list[str] = []
        try:
            with ThreadPoolExecutor(max_workers=len(repositories)) as executor:
                created_paths = list(executor.map(instrument, repositories))

            self.assertEqual(len(set(created_paths)), len(repositories))
            for path, repository in zip(created_paths, repositories):
                with open(path) as dockerfile:
                    content = dockerfile.read()
                self.assertIn(f"service.name={repository}", content)
                self.assertNotIn(".name=", content.split("ENV OTEL_RESOURCE_ATTRIBUTES", 1)[0])
        finally:
            for path in created_paths:
                if os.path.isfile(path):
                    os.unlink(path)


if __name__ == "__main__":
    unittest.main()
