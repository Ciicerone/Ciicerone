"""Client data management commands for Ciicerone CLI."""

import click


@click.group()
def client_data():
    """Manage client data for threat simulations."""
    pass


@client_data.command("list")
def list_clients():
    """List all registered clients."""
    click.echo("No clients registered yet.")


@client_data.command("add")
@click.option("--name", "-n", required=True, help="Client name")
@click.option("--industry", "-i", default="general", help="Client industry")
def add_client(name: str, industry: str):
    """Add a new client."""
    click.echo(f"Adding client: {name} ({industry})")
