#!/usr/bin/env python3
import click
from narwhal.pr_writer import create_pr

@click.group()
def cli():
    """Narwhal (nh) — Agentic AI PR creator."""
    pass

@cli.command(name="pr")
@click.argument("action", default="create")
def pr_cmd(action):
    """nh pr create  → generate and open a PR."""
    if action == "create":
        create_pr()
    else:
        click.echo(f"Unknown action: {action}")

if __name__ == "__main__":
    cli()