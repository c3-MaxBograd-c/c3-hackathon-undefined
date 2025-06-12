#!/usr/bin/env python3
# -------------------------------------------------------------------
# CLI entry point for Beluga (bl)
# -------------------------------------------------------------------
# This file defines your top-level `bl` command and its subcommands.
# 
# How it works:
#   - Uses Click to parse `bl <command> [args]`.
#   - The `cli()` group is what setuptools points to via console_scripts.
#
# What to invoke:
#   - `bl pr create` → calls create_pr() in pr_writer.py
#   - You can add new commands by decorating functions with @cli.command()
#
# Where to extend:
#   - To add `bl foo`, write:
#       @cli.command()
#       def foo(): …
#     and import your logic module here.
#
# What not to change:
#   - The @cli.group() and the entry-point definition `bl = "beluga.cli:cli"`
#     in pyproject.toml.
#
import click
from beluga.pr_writer import create_pr

@click.group()
def cli():
    """Beluga (bl) — Agentic AI PR creator."""
    # ======== NO CHANGES BELOW THIS LINE =============
    pass

@cli.command(name="pr")
@click.argument("action", default="create")
def pr_cmd(action):
    """
    bl pr create        → generate and open a PR.
    """
    if action == "create":
        create_pr()
    else:
        click.echo(f"Unknown action: {action}")

# To add another subcommand group under `bl`, add more @cli.command() here.

if __name__ == "__main__":
    cli()