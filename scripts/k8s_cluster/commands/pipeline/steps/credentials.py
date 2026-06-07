import os

from k8s_cluster.commands.pipeline.log import log_step_detail
from k8s_cluster.commands.pipeline.steps.shell import write_secrets_to_file
from k8s_cluster.commands.pipeline.types import CredentialsStepArgs
from k8s_cluster.paths import REPO_ROOT


def handle_credentials_step(args: CredentialsStepArgs, temp_folder_path: str) -> int:
    log_step_detail(f"Writing credentials to {args.output_file} from vault path {args.path}")
    resource, target, namespace = args.path.split(":")
    all_secrets = {}
    vault_root = os.path.join(REPO_ROOT, "resources", "vault", target)
    resource_directories = os.listdir(vault_root)
    for resource_name in resource_directories:
        if resource_name != resource:
            continue
        env_dir = os.path.join(vault_root, resource_name, namespace)
        if not os.path.isdir(env_dir):
            continue

        with open(os.path.join(env_dir, ".env")) as secrets_file:
            lines = secrets_file.readlines()
            for line in lines:
                key, value = line.split("=")
                all_secrets[f"{resource_name.upper()}_{key.upper()}"] = value.strip()

    credentials_path = os.path.join(temp_folder_path, args.output_file.lstrip("./"))
    write_secrets_to_file(all_secrets, credentials_path)
    log_step_detail(f"Wrote {len(all_secrets)} credential(s) to {credentials_path}")

    return 0
