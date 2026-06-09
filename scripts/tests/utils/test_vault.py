import os
import tempfile
import unittest
from unittest.mock import patch

from k8s_cluster.utils.vault import (
    exclude_infra_only_keys,
    get_secrets_for_app,
    load_vault_env,
    normalize_database_secret_env,
    resolve_database_host,
)


class TestVaultHelpers(unittest.TestCase):
    def test_resolve_database_host_defaults_to_postgresql(self):
        self.assertEqual(resolve_database_host({}), "postgresql")
        self.assertEqual(resolve_database_host({"DATABASE_CLUSTER_HOST": "custom-pg"}), "custom-pg")

    def test_normalize_database_secret_env_sets_host_and_port(self):
        secrets = {
            "DATABASE_USER": "root",
            "DATABASE_PASSWORD": "example",
            "DATABASE_NAME": "kafka-worker",
            "DATABASE_CLUSTER_HOST": "postgresql",
        }
        normalized = normalize_database_secret_env(secrets)
        self.assertEqual(normalized["DATABASE_HOST"], "postgresql")
        self.assertEqual(normalized["DATABASE_PORT"], "5432")
        self.assertNotIn("DATABASE_CLUSTER_HOST", normalized)

    def test_exclude_infra_only_keys_removes_localstack_token(self):
        secrets = {
            "AWS_ACCESS_KEY_ID": "test",
            "AWS_LOCALSTACK_AUTH_TOKEN": "secret",
        }
        filtered = exclude_infra_only_keys(secrets, "aws")
        self.assertEqual(filtered, {"AWS_ACCESS_KEY_ID": "test"})

    def test_load_vault_env_prefixes_keys_and_skips_missing_dirs(self):
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = os.path.join(temp_root, "repo")
            target_dir = os.path.join(repo_root, "resources", "vault", "kafka-worker", "database", "dev")
            os.makedirs(target_dir)
            with open(os.path.join(target_dir, ".env"), "w") as env_file:
                env_file.write("USER=root\nCLUSTER_HOST=postgresql\n")

            with patch("k8s_cluster.utils.vault.REPO_ROOT", repo_root):
                secrets = load_vault_env("kafka-worker", "dev")
                self.assertEqual(secrets["DATABASE_USER"], "root")
                self.assertEqual(secrets["DATABASE_CLUSTER_HOST"], "postgresql")
                self.assertEqual(load_vault_env("missing-repo", "dev"), {})

    def test_get_secrets_for_app_merges_shared_vault_when_opted_in(self):
        with tempfile.TemporaryDirectory() as temp_root:
            repo_root = os.path.join(temp_root, "repo")
            worker_db = os.path.join(repo_root, "resources", "vault", "kafka-worker", "database", "dev")
            admin_aws = os.path.join(repo_root, "resources", "vault", "_admin", "aws", "dev")
            os.makedirs(worker_db)
            os.makedirs(admin_aws)

            with open(os.path.join(worker_db, ".env"), "w") as env_file:
                env_file.write("USER=root\nPASSWORD=example\nNAME=kafka-worker\nCLUSTER_HOST=postgresql\n")
            with open(os.path.join(admin_aws, ".env"), "w") as env_file:
                env_file.write("ACCESS_KEY_ID=test\nSECRET_ACCESS_KEY=test\nLOCALSTACK_AUTH_TOKEN=infra-only\n")

            with patch("k8s_cluster.utils.vault.REPO_ROOT", repo_root):
                without_shared = get_secrets_for_app("kafka-worker", "dev", [])
                self.assertIn("DATABASE_USER", without_shared)
                self.assertNotIn("AWS_ACCESS_KEY_ID", without_shared)

                with_shared = get_secrets_for_app("kafka-worker", "dev", ["aws"])
                self.assertEqual(with_shared["AWS_ACCESS_KEY_ID"], "test")
                self.assertNotIn("AWS_LOCALSTACK_AUTH_TOKEN", with_shared)
                self.assertEqual(with_shared["DATABASE_HOST"], "postgresql")


if __name__ == "__main__":
    unittest.main()
