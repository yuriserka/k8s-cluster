import typer

from k8s_cluster.cli import exit_on_failure, make_cli_app
from k8s_cluster.commands.database.service import create_database
from k8s_cluster.commands.database.types import CreateDatabaseRequest

app = make_cli_app()


@app.command("create")
def create(
    namespace: str = typer.Option(..., help="Kubernetes namespace (e.g. dev)"),
    repository: str = typer.Option(..., help="App folder under apps/"),
) -> None:
    try:
        exit_code = create_database(CreateDatabaseRequest(repository=repository, namespace=namespace))
    except (FileNotFoundError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    exit_on_failure(exit_code, "")
