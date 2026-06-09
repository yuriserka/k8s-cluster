import tempfile
import unittest
from unittest.mock import patch

from k8s_cluster.commands.app.install_service import (
    apply_api_allowed_hosts,
    build_install_values,
    handle_probes,
    resolve_allowed_hosts,
    resolve_component_label,
    resolve_helm_names,
    resolve_service_enabled,
)
from k8s_cluster.commands.app.types import InstallAppRequest


class TestHandleProbes(unittest.TestCase):
    def test_strips_incomplete_probes(self):
        values = {
            "livenessProbe": None,
            "readinessProbe": None,
            "startupProbe": None,
        }
        handle_probes(values)
        self.assertIsNone(values["livenessProbe"])
        self.assertIsNone(values["readinessProbe"])
        self.assertIsNone(values["startupProbe"])

    def test_http_probe_path_sets_startup_probe(self):
        values = {
            "livenessProbe": None,
            "readinessProbe": None,
            "startupProbe": None,
        }
        handle_probes(values, "livenessProbePath", "/metrics")
        self.assertEqual(values["livenessProbe"]["httpGet"]["path"], "/metrics")
        self.assertEqual(values["livenessProbe"]["httpGet"]["httpHeaders"], [{"name": "Host", "value": "localhost"}])
        self.assertEqual(values["startupProbe"]["httpGet"]["path"], "/metrics")

    def test_exec_probe_cmd_sets_startup_probe(self):
        values = {
            "livenessProbe": None,
            "readinessProbe": None,
            "startupProbe": None,
        }
        command = ["python", "worker_health_check.py"]
        handle_probes(values, "livenessProbeCmd", command)
        self.assertEqual(values["livenessProbe"]["exec"]["command"], command)
        self.assertEqual(values["startupProbe"]["exec"]["command"], command)


class TestResolveHelmMetadata(unittest.TestCase):
    def test_resolve_helm_names(self):
        self.assertEqual(
            resolve_helm_names("kafka-worker-api", "dev"),
            ("kafka-worker-api", "kafka-worker-api-dev"),
        )

    def test_resolve_component_label_api(self):
        self.assertEqual(
            resolve_component_label({"component": "api"}),
            {"app.kubernetes.io/component": "api"},
        )

    def test_resolve_component_label_worker(self):
        self.assertEqual(
            resolve_component_label({"component": "worker"}),
            {"app.kubernetes.io/component": "worker"},
        )

    def test_resolve_component_label_rejects_invalid(self):
        with self.assertRaises(ValueError):
            resolve_component_label({"component": "scheduler"})

    def test_resolve_service_enabled_api_requires_port(self):
        self.assertTrue(resolve_service_enabled("api", {"port": 8000}))
        with self.assertRaises(ValueError):
            resolve_service_enabled("api", {})

    def test_resolve_allowed_hosts(self):
        self.assertEqual(
            resolve_allowed_hosts("kafka-worker-api-dev"),
            "localhost,127.0.0.1,kafka-worker-api-dev-service,.svc.cluster.local",
        )

    def test_apply_api_allowed_hosts_injects_for_api(self):
        values = {"env": {"KAFKA_BOOTSTRAP_SERVERS": "kafka:9092"}}
        apply_api_allowed_hosts(values, "api", "kafka-worker-api-dev")
        self.assertEqual(
            values["env"]["ALLOWED_HOSTS"],
            "localhost,127.0.0.1,kafka-worker-api-dev-service,.svc.cluster.local",
        )

    def test_apply_api_allowed_hosts_skips_worker(self):
        values = {"env": {}}
        apply_api_allowed_hosts(values, "worker", "kafka-worker-scheduler-dev")
        self.assertNotIn("ALLOWED_HOSTS", values["env"])

    def test_apply_api_allowed_hosts_respects_kube_override(self):
        values = {"env": {"ALLOWED_HOSTS": "custom.example"}}
        apply_api_allowed_hosts(values, "api", "kafka-worker-api-dev")
        self.assertEqual(values["env"]["ALLOWED_HOSTS"], "custom.example")

    def test_resolve_service_enabled_worker_depends_on_port(self):
        self.assertFalse(resolve_service_enabled("worker", {}))
        self.assertTrue(resolve_service_enabled("worker", {"port": 8005}))


class TestBuildInstallValues(unittest.TestCase):
    def _write_file(self, path: str, content: str) -> None:
        import os

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as file:
            file.write(content)

    def test_splits_env_and_secret_env_and_honors_vault_shared(self):
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = temp_root
            envs_dev = f"{repo_root}/envs/dev"
            kube_dir = f"{repo_root}/apps/kafka-worker/kube/dev"
            resources_dir = f"{repo_root}/resources/kafka-worker-api"
            worker_vault = f"{repo_root}/resources/vault/kafka-worker/database/dev"
            admin_aws = f"{repo_root}/resources/vault/_admin/aws/dev"

            self._write_file(
                f"{envs_dev}/values.yaml",
                """
replicaCount: 1
image:
  repository: ""
  pullPolicy: Never
  tag: ""
container:
  cmd: null
  args: []
service:
  enabled: true
  type: ClusterIP
  port: 80
env: {}
secretEnv: {}
resources: {}
livenessProbe: null
readinessProbe: null
startupProbe: null
autoscaling:
  enabled: false
""",
            )
            self._write_file(
                f"{kube_dir}/api.yaml",
                """
vaultShared:
  - aws
env:
  KAFKA_BOOTSTRAP_SERVERS: kafka:9092
livenessProbePath: /metrics
readinessProbePath: /metrics
port: 8000
""",
            )
            self._write_file(
                f"{resources_dir}/dev.yaml",
                """
component: api
autoscaling:
  enabled: false
resources:
  requests:
    cpu: 100m
    memory: 256Mi
""",
            )
            self._write_file(
                f"{worker_vault}/.env",
                "USER=root\nPASSWORD=example\nNAME=kafka-worker\nCLUSTER_HOST=postgresql\n",
            )
            self._write_file(
                f"{admin_aws}/.env",
                "ACCESS_KEY_ID=test\nSECRET_ACCESS_KEY=test\nLOCALSTACK_AUTH_TOKEN=infra-only\n",
            )

            request = InstallAppRequest(
                application="kafka-worker-api",
                repository="kafka-worker",
                params_file="api.yaml",
                app_path=f"{repo_root}/apps/kafka-worker",
                namespace="dev",
                tag="dev",
                pipeline_id=None,
                pipeline_started_at=None,
            )

            with patch("k8s_cluster.commands.app.install_service.REPO_ROOT", repo_root):
                with patch("k8s_cluster.utils.vault.REPO_ROOT", repo_root):
                    values, _ = build_install_values(request, "dev")

            self.assertEqual(
                values["env"],
                {
                    "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092",
                    "ALLOWED_HOSTS": "localhost,127.0.0.1,kafka-worker-api-dev-service,.svc.cluster.local",
                },
            )
            self.assertEqual(values["nameOverride"], "kafka-worker-api")
            self.assertEqual(values["fullnameOverride"], "kafka-worker-api-dev")
            self.assertEqual(values["podLabels"], {"app.kubernetes.io/component": "api"})
            self.assertTrue(values["service"]["enabled"])
            self.assertEqual(values["service"]["port"], 8000)
            self.assertNotIn("component", values)
            self.assertEqual(values["secretEnv"]["DATABASE_PASSWORD"], "example")
            self.assertEqual(values["secretEnv"]["AWS_ACCESS_KEY_ID"], "test")
            self.assertNotIn("AWS_LOCALSTACK_AUTH_TOKEN", values["secretEnv"])
            self.assertNotIn("vaultShared", values)
            self.assertEqual(values["livenessProbe"]["httpGet"]["path"], "/metrics")
            self.assertIsNone(values.get("livenessProbePath"))

    def test_scheduler_without_vault_shared_has_no_aws_secrets(self):
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = temp_root
            envs_dev = f"{repo_root}/envs/dev"
            kube_dir = f"{repo_root}/apps/kafka-worker/kube/dev"
            resources_dir = f"{repo_root}/resources/kafka-worker-scheduler"
            worker_vault = f"{repo_root}/resources/vault/kafka-worker/database/dev"
            admin_aws = f"{repo_root}/resources/vault/_admin/aws/dev"

            self._write_file(
                f"{envs_dev}/values.yaml",
                """
image:
  repository: ""
  pullPolicy: Never
  tag: ""
container:
  cmd: null
  args: []
service:
  enabled: true
  type: ClusterIP
  port: 80
env: {}
secretEnv: {}
resources: {}
livenessProbe: null
readinessProbe: null
startupProbe: null
autoscaling:
  enabled: false
""",
            )
            self._write_file(
                f"{kube_dir}/scheduler.yaml",
                """
livenessProbeCmd:
  - python
  - worker_health_check.py
readinessProbeCmd:
  - python
  - worker_health_check.py
""",
            )
            self._write_file(
                f"{resources_dir}/dev.yaml",
                "component: worker\nautoscaling:\n  enabled: false\n",
            )
            self._write_file(
                f"{worker_vault}/.env",
                "USER=root\nPASSWORD=example\nNAME=kafka-worker\nCLUSTER_HOST=postgresql\n",
            )
            self._write_file(
                f"{admin_aws}/.env",
                "ACCESS_KEY_ID=test\nSECRET_ACCESS_KEY=test\n",
            )

            request = InstallAppRequest(
                application="kafka-worker-scheduler",
                repository="kafka-worker",
                params_file="scheduler.yaml",
                app_path=f"{repo_root}/apps/kafka-worker",
                namespace="dev",
                tag="dev",
                pipeline_id=None,
                pipeline_started_at=None,
            )

            with patch("k8s_cluster.commands.app.install_service.REPO_ROOT", repo_root):
                with patch("k8s_cluster.utils.vault.REPO_ROOT", repo_root):
                    values, _ = build_install_values(request, "dev")

            self.assertFalse(values["service"]["enabled"])
            self.assertEqual(values["nameOverride"], "kafka-worker-scheduler")
            self.assertEqual(values["fullnameOverride"], "kafka-worker-scheduler-dev")
            self.assertEqual(values["podLabels"], {"app.kubernetes.io/component": "worker"})
            self.assertNotIn("AWS_ACCESS_KEY_ID", values["secretEnv"])
            self.assertEqual(values["livenessProbe"]["exec"]["command"], ["python", "worker_health_check.py"])

    def test_api_without_port_raises(self):
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = temp_root
            self._write_file(
                f"{repo_root}/envs/dev/values.yaml",
                """
image:
  repository: ""
  pullPolicy: Never
  tag: ""
service:
  enabled: true
  port: 80
""",
            )
            self._write_file(
                f"{repo_root}/apps/kafka-worker/kube/dev/api.yaml",
                "env: {}\n",
            )
            self._write_file(
                f"{repo_root}/resources/kafka-worker-api/dev.yaml",
                "component: api\n",
            )
            self._write_file(
                f"{repo_root}/resources/vault/kafka-worker/database/dev/.env",
                "USER=root\nPASSWORD=x\nNAME=kafka-worker\nCLUSTER_HOST=postgresql\n",
            )

            request = InstallAppRequest(
                application="kafka-worker-api",
                repository="kafka-worker",
                params_file="api.yaml",
                app_path=f"{repo_root}/apps/kafka-worker",
                namespace="dev",
                tag="dev",
                pipeline_id=None,
                pipeline_started_at=None,
            )

            with patch("k8s_cluster.commands.app.install_service.REPO_ROOT", repo_root):
                with patch("k8s_cluster.utils.vault.REPO_ROOT", repo_root):
                    with self.assertRaises(ValueError):
                        build_install_values(request, "dev")


if __name__ == "__main__":
    unittest.main()
