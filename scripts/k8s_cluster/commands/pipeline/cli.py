import os

import typer

from k8s_cluster.cli import make_cli_app
from k8s_cluster.commands.pipeline.runner import run_pipeline
from k8s_cluster.paths import SCRIPT_DIR

app = make_cli_app()


@app.command("run")
def run(
    repository: str = typer.Argument(..., help="App folder under apps/ (e.g. kafka-worker)"),
) -> None:
    os.chdir(SCRIPT_DIR)
    run_pipeline(repository)
