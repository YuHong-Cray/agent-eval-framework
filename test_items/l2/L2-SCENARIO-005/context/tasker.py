"""Task Manager CLI ¡ª implement the subcommands below."""
import click

@click.group()
def cli():
    """A simple task manager."""
    pass

@cli.command()
@click.argument("title")
def add(title):
    """Add a new task."""
    # TODO: implement
    pass

if __name__ == "__main__":
    cli()
