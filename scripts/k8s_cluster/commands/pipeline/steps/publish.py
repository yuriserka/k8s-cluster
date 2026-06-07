from k8s_cluster.commands.app.publish_service import publish_app
from k8s_cluster.commands.app.types import PublishAppRequest
from k8s_cluster.commands.pipeline.log import log_step_detail
from k8s_cluster.commands.pipeline.types import PublishStepArgs


def handle_publish_step(args: PublishStepArgs, temp_folder_path: str) -> int:
    image = f"{args.repo}-{args.env}:{args.env}"
    log_step_detail(f"Building image {image} from {args.dockerfile}")
    if args.build_args:
        log_step_detail(f"Docker build args: {args.build_args}")
    return publish_app(
        PublishAppRequest(
            repository=args.repo,
            dockerfile=args.dockerfile,
            app_path=temp_folder_path,
            namespace=args.env,
            tag=args.env,
            use_minikube_docker=True,
            build_args=args.build_args or None,
        )
    )
