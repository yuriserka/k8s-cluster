import os

from k8s_cluster.commands.pipeline.log import log_step_detail
from k8s_cluster.commands.pipeline.steps.shell import write_secrets_to_file
from k8s_cluster.commands.pipeline.types import CredentialsStepArgs
from k8s_cluster.utils.vault import load_vault_env


def handle_credentials_step(args: CredentialsStepArgs, temp_folder_path: str) -> int:
    log_step_detail(f"Writing credentials to {args.output_file} from vault path {args.path}")
    resource, target, namespace = args.path.split(":")
    all_secrets = load_vault_env(target, namespace, include_resources={resource})

    credentials_path = os.path.join(temp_folder_path, args.output_file.lstrip("./"))
    write_secrets_to_file(all_secrets, credentials_path)
    log_step_detail(f"Wrote {len(all_secrets)} credential(s) to {credentials_path}")

    return 0
