import unittest

from k8s_cluster.commands.pipeline.loader import parse_step_args
from k8s_cluster.commands.pipeline.types import (
    CredentialsStepArgs,
    DatabaseMigrationStepArgs,
    InstallStepArgs,
    PublishStepArgs,
)


class TestParseStepArgs(unittest.TestCase):
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
