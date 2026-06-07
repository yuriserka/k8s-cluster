from k8s_cluster.commands.app.install_service import install_app
from k8s_cluster.commands.app.types import InstallAppRequest
from k8s_cluster.commands.pipeline.types import InstallStepArgs
from k8s_cluster.services.pod_wait import READY_TIMEOUT_SECONDS, wait_for_deployment_rollout


def handle_install_step(
    args: InstallStepArgs,
    temp_folder_path: str,
    pipeline_id: str,
    pipeline_started_at: str,
) -> int:
    print("Installing app with args:", args)
    exit_code = install_app(
        InstallAppRequest(
            application=args.application,
            repository=args.repo,
            params_file=args.params_file,
            app_path=temp_folder_path,
            namespace=args.env,
            tag=args.env,
            pipeline_id=pipeline_id,
            pipeline_started_at=pipeline_started_at,
        )
    )
    if exit_code != 0:
        return exit_code

    return wait_for_deployment_rollout(
        args.application,
        args.env,
        pipeline_id,
        timeout_seconds=READY_TIMEOUT_SECONDS,
    )
