import unittest

from k8s_cluster.commands.pipeline.loader import parse_step_args, strip_step_metadata
from k8s_cluster.commands.pipeline.types import (
    CloneStepArgs,
    CredentialsStepArgs,
    DatabaseMigrationStepArgs,
    InstallStepArgs,
    PublishStepArgs,
)


class TestParseStepArgs(unittest.TestCase):
    def test_clone(self):
        args = parse_step_args("clone", {"kind": "clone"})
        self.assertIsInstance(args, CloneStepArgs)

    def test_strip_step_metadata(self):
        stripped = strip_step_metadata({"kind": "publish", "depends_on": "test", "repo": "x", "env": "dev"})
        self.assertNotIn("depends_on", stripped)
        self.assertEqual(stripped["repo"], "x")

    def test_database_migration(self):
        args = parse_step_args(
            "database_migration",
            {
                "kind": "database_migration",
                "env": "dev",
                "repository": "kafka-worker",
                "image_repo": "kafka-worker-api",
                "cmd": ["python manage.py migrate"],
            },
        )
        self.assertIsInstance(args, DatabaseMigrationStepArgs)
        self.assertEqual(args.repository, "kafka-worker")

    def test_credentials(self):
        args = parse_step_args(
            "credentials",
            {"kind": "credentials", "path": "database:kafka-worker:dev", "output_file": "./db.env"},
        )
        self.assertIsInstance(args, CredentialsStepArgs)

    def test_install(self):
        args = parse_step_args(
            "install",
            {
                "kind": "install",
                "repo": "kafka-worker",
                "application": "kafka-worker-api",
                "params_file": "api.yaml",
                "env": "dev",
            },
        )
        self.assertIsInstance(args, InstallStepArgs)

    def test_publish(self):
        args = parse_step_args(
            "publish",
            {
                "kind": "publish",
                "repo": "kafka-worker-api",
                "dockerfile": "Dockerfile",
                "env": "dev",
                "build_args": {"CONTAINER": "api"},
            },
        )
        self.assertIsInstance(args, PublishStepArgs)
        self.assertEqual(args.build_args, {"CONTAINER": "api"})
