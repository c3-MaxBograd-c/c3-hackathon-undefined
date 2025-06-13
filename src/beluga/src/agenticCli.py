#!/usr/bin/env python3
# -------------------------------------------------------------------
# CLI entry point for Beluga (beluga)
# -------------------------------------------------------------------
# This file defines your top-level `beluga` command and its subcommands.
# 
# How it works:
#   - Uses Click to parse `beluga <command> [args]`.
#   - The `cli()` group is what setuptools points to via console_scripts.
#
# What to invoke:
#   - `beluga pr create` → calls create_pr() in pr_writer.py
#   - `beluga pr create --dry-run` → generates PR content, shows preview, asks for confirmation
#   - `beluga pr update` → calls update_pr() in pr_writer.py (TODO)
#   - `beluga pr` (no action) → shows available pr actions
#   - You can add new commands by decorating functions with @cli.command()
#
# Where to extend:
#   - For new PR actions, add elif branches in pr_cmd()
#   - For new top-level commands, add @cli.command() decorators below pr_cmd
#   - Update valid_actions list when adding new PR actions
#
# What not to change:
#   - The @click.group() decorator and the entry-point definition
#     `beluga = "beluga.cli:cli"` in pyproject.toml.
#   - The main() function signature (console_scripts expects it)
# -------------------------------------------------------------------

import sys
import click

from beluga.src import messages
from beluga.src.testHook import makeRestCall

# =============================================================================
# TOP-LEVEL CLI GROUP
# =============================================================================

@click.group(
    help=messages.CLI_DESC,
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": 120,  # wider help text for readability
    },
    invoke_without_command=True,
)

@click.version_option("0.1.0", prog_name="beluga")
@click.pass_context
def cli(ctx):
    """
    Main CLI entry point. Handles the top-level `beluga` command.
    """
    makeRestCall()

def main():
    """
    Console script entry point defined in pyproject.toml.
    
    This function:
    1. Wraps the Click CLI with top-level exception handling
    2. Ensures clean exit codes for shell scripting
    3. Provides user-friendly error messages for unexpected failures
    
    Exit codes:
    - 0: successful execution
    - 1: application error (from subcommands)
    - 2: invalid input (from subcommands) 
    - 3: unexpected system error (caught here)
    
    Do not modify this function unless you understand Click's exception handling.
    """
    try:
        cli()
    except click.ClickException as ce:
        # Click's built-in exceptions (bad arguments, etc.)
        # Click will automatically show the error and help text
        ce.show()
        sys.exit(ce.exit_code)
    except KeyboardInterrupt:
        # User pressed Ctrl+C
        click.echo(f"\n{messages.ERR_OPERATION_CANCELLED}", err=True)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        # Catch-all for truly unexpected errors (should be rare)
        click.secho(messages.ERR_UNEXPECTED_SYSTEM.format(error=e), fg="red", err=True)
        click.echo(messages.HELP_BUG_REPORT)
        sys.exit(3)  # Exit code 3 = unexpected system error

# Allow running this file directly for testing
if __name__ == "__main__":
    main()