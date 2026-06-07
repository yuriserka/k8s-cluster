import io
import unittest
from contextlib import redirect_stdout

from k8s_cluster.commands.pipeline.log import (
    SEPARATOR_MAJOR,
    SEPARATOR_MINOR,
    log_step_end,
    log_step_start,
    summarize_step,
)


class TestSummarizeStep(unittest.TestCase):
    def test_shell_step(self):
        lines = summarize_step(
            "lint",
            {"cmd": [". .venv/bin/activate && python code_checks.py"]},
        )
        self.assertEqual(lines[0], "commands: 1")
        self.assertTrue(lines[1].startswith("first: "))

    def test_publish_step(self):
        lines = summarize_step(
            "dev-publish-api",
            {
                "kind": "publish",
                "repo": "kafka-worker-api",
                "env": "dev",
                "dockerfile": "kafkaworker/containers/Dockerfile",
                "build_args": {"CONTAINER": "api"},
            },
        )
        self.assertIn("repository: kafka-worker-api", lines)
        self.assertIn("env: dev  |  image: kafka-worker-api-dev:dev", lines)
        self.assertIn("build_args: {'CONTAINER': 'api'}", lines)

    def test_install_step(self):
        lines = summarize_step(
            "dev-deploy-api",
            {
                "kind": "install",
                "repo": "kafka-worker",
                "application": "kafka-worker-api",
                "params_file": "api.yaml",
                "env": "dev",
            },
        )
        self.assertIn("application: kafka-worker-api", lines)
        self.assertIn("env: dev  |  release: kafka-worker-api", lines)

    def test_database_migration_step(self):
        lines = summarize_step(
            "dev-migrate",
            {
                "kind": "database_migration",
                "env": "dev",
                "repository": "kafka-worker",
                "image_repo": "kafka-worker-api",
                "cmd": ["python manage.py migrate"],
            },
        )
        self.assertIn("repository: kafka-worker", lines)
        self.assertIn("migrate_commands: 1", lines)


class TestStepHeaders(unittest.TestCase):
    def test_log_step_start_contains_index_kind_and_separator(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            log_step_start(3, 10, "lint", "shell", ["commands: 1"])
        output = buffer.getvalue()
        self.assertIn(SEPARATOR_MAJOR, output)
        self.assertIn("STEP 3/10: lint  |  kind: shell", output)
        self.assertIn("  commands: 1", output)

    def test_log_step_end_success(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            log_step_end(3, 10, "lint", 0, 4.2)
        output = buffer.getvalue()
        self.assertIn(SEPARATOR_MINOR, output)
        self.assertIn("STEP 3/10: lint  finished in 4.2s  (exit 0)", output)

    def test_log_step_end_failure(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            log_step_end(3, 10, "lint", 1, 2.0)
        output = buffer.getvalue()
        self.assertIn("FAILED in 2.0s  (exit 1)", output)


if __name__ == "__main__":
    unittest.main()
