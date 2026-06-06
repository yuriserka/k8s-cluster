import typer


def make_cli_app() -> typer.Typer:
    return typer.Typer(add_completion=False, no_args_is_help=True)


def exit_on_failure(exit_code: int, message: str) -> None:
    if exit_code != 0:
        if message:
            typer.echo(message, err=True)
        raise typer.Exit(code=exit_code)
