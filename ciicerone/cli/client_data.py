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
