"""Quantum-safe cryptography commands for Ciicerone CLI."""

import click


@click.group()
def quantum():
    """Manage quantum-safe cryptographic operations."""
    pass


@quantum.command("generate")
def generate_key():
    """Generate a quantum-safe key."""
    click.echo("Quantum key generation placeholder.")
