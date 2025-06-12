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
#   - The @click.group() decorator and the entry-point definition
#     `bl = "beluga.cli:cli"` in pyproject.toml.
# -------------------------------------------------------------------

import sys
import click

from beluga.pr_writer import create_pr
from beluga.messages import (
    CLI_DESC,
    PR_HELP,
    PR_ACTION_HELP,
    ERR_PR_FAILURE,
    ERR_UNKNOWN_ACTION,
)

@click.group(
    help=CLI_DESC,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.version_option("0.1.0", prog_name="bl")
@click.pass_context
def cli(ctx):
    """Beluga (bl) — Agentic AI PR creator."""
    # ======== NO CHANGES BELOW THIS LINE =============
    # If no subcommand is provided, show top-level help and exit
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)

@cli.command(
    name="pr",
    help=PR_HELP
)
@click.argument("action", required=False, metavar="[create]")
@click.pass_context
def pr_cmd(ctx, action):
    """
    bl pr create        → generate and open a PR.
    """
    # default behavior is 'create'
    action = action or "create"

    if action == "create":
        try:
            create_pr()
        except Exception as e:
            # catch errors from create_pr() and exit gracefully
            click.secho(
                ERR_PR_FAILURE.format(error=str(e)),
                fg="red",
                err=True
            )
            ctx.exit(1)
    else:
        # unknown action
        click.secho(
            ERR_UNKNOWN_ACTION.format(action=action),
            fg="yellow",
            err=True
        )
        click.echo(PR_ACTION_HELP)
        ctx.exit(2)

# To add another subcommand under `bl`, define a new @cli.command() here.

def main():
    """
    Entry point for console_scripts.
    Wraps cli() to handle uncaught exceptions.
    """
    try:
        cli()
    except click.ClickException as ce:
        # Click will render its own usage and error message
        ce.show()
        sys.exit(ce.exit_code)
    except Exception as e:
        # Catch-all for unexpected errors
        click.secho(f"❌ Unexpected error: {e}", fg="red", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()