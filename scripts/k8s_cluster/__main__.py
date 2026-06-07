import typer

from k8s_cluster.commands.app.cli import app as app_cli
from k8s_cluster.commands.database.cli import app as database_cli
from k8s_cluster.commands.infra.cli import app as infra_cli
from k8s_cluster.commands.pipeline.cli import app as pipeline_cli

app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(pipeline_cli, name="pipeline")
app.add_typer(infra_cli, name="infra")
app.add_typer(app_cli, name="app")
app.add_typer(database_cli, name="database")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
