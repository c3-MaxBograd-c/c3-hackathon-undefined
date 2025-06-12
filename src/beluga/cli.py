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
#   - For new PR actions, add elif branches in pr_cmd()
#   - For new top-level commands, add @cli.command() decorators below pr_cmd
#
# What not to change:
#   - The @click.group() decorator and the entry-point definition
#     `bl = "beluga.cli:cli"` in pyproject.toml.
#   - The main() function signature (console_scripts expects it)
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

# =============================================================================
# TOP-LEVEL CLI GROUP
# =============================================================================

@click.group(
    help=CLI_DESC,
    context_settings={
        "help_option_names": ["-h", "--help"],
        "max_content_width": 120,  # wider help text for readability
    },
    invoke_without_command=True,
)
@click.version_option("0.1.0", prog_name="bl")
@click.pass_context
def cli(ctx):
    """
    Main CLI entry point. Handles the top-level `bl` command.
    
    Behavior:
    - If no subcommand is given (e.g., just `bl`), shows help and exits cleanly
    - If subcommand is given (e.g., `bl pr`), delegates to that handler
    - Click automatically handles --help, --version, and unknown subcommands
    """
    # ======== NO CHANGES BELOW THIS LINE =============
    # If no subcommand is provided, show top-level help and exit gracefully
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)  # Use ctx.exit(0) instead of sys.exit(0) for Click consistency

# =============================================================================
# PR SUBCOMMAND
# =============================================================================

@cli.command(
    name="pr",
    help=PR_HELP,
    context_settings={"allow_extra_args": False, "allow_interspersed_args": False}
)
@click.argument("action", required=False, metavar="[create|update]")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without actually creating/updating the PR"
)
@click.pass_context
def pr_cmd(ctx, action, dry_run):
    """
    Handles all `bl pr <action>` commands.
    
    Input validation:
    - action: optional string, defaults to "create" if not provided
    - dry_run: optional flag for testing without side effects
    
    Behavior:
    - "create": calls create_pr() and handles success/failure
    - "update": (future) calls update_pr() 
    - unknown action: shows error + help, exits with code 2
    - any exception from pr_writer: shows error, exits with code 1
    
    Exit codes:
    - 0: success
    - 1: PR operation failed (network, auth, validation, etc.)
    - 2: invalid user input (unknown action)
    """
    
    # Input normalization and validation
    if action is None or action.strip() == "":
        action = "create"  # default behavior
    else:
        action = action.lower().strip()  # normalize user input
    
    # Validate action is supported
    valid_actions = ["create", "update"]
    if action not in valid_actions:
        click.secho(
            ERR_UNKNOWN_ACTION.format(action=action),
            fg="yellow",
            err=True
        )
        click.echo(f"Valid actions: {', '.join(valid_actions)}")
        click.echo(f"\nRun 'bl pr --help' for more information.")
        ctx.exit(2)  # Exit code 2 = invalid user input
    
    # Handle each supported action
    if action == "create":
        _handle_pr_create(ctx, dry_run)
    elif action == "update":
        _handle_pr_update(ctx, dry_run)
    # Note: we've already validated action above, so no else needed

def _handle_pr_create(ctx, dry_run):
    """
    Handles `bl pr create` command execution.
    
    Args:
        ctx: Click context for error handling
        dry_run: boolean flag for testing mode
    
    Behavior:
    - Shows user-friendly status messages
    - Calls create_pr() from pr_writer module
    - On success: shows success message, exits 0
    - On failure: shows error message, exits 1
    """
    try:
        if dry_run:
            click.echo("🔍 DRY RUN: Would create a new PR (no actual changes)")
            # TODO: implement dry-run logic in pr_writer
            return
        
        click.echo("🚀 Creating new PR...")
        
        # Call the actual PR creation logic
        result = create_pr()  # Should return URL or success info
        
        # Handle success (create_pr should return something useful)
        if result:
            click.secho(f"✅ PR created successfully: {result}", fg="green")
        else:
            click.secho("✅ PR created successfully", fg="green")
            
    except FileNotFoundError as e:
        # Handle missing files (git repo, config, etc.)
        click.secho(f"❌ File not found: {e}", fg="red", err=True)
        click.echo("Make sure you're in a git repository with changes to commit.")
        ctx.exit(1)
        
    except PermissionError as e:
        # Handle permission issues (git, file system, etc.)
        click.secho(f"❌ Permission denied: {e}", fg="red", err=True)
        click.echo("Check your file permissions and git repository access.")
        ctx.exit(1)
        
    except Exception as e:
        # Catch-all for any other errors from pr_writer
        click.secho(
            ERR_PR_FAILURE.format(error=str(e)),
            fg="red",
            err=True
        )
        
        # Provide helpful context based on error type
        error_str = str(e).lower()
        if "authentication" in error_str or "token" in error_str:
            click.echo("💡 Hint: Check your GitHub token in the .env file")
        elif "network" in error_str or "connection" in error_str:
            click.echo("💡 Hint: Check your internet connection")
        elif "git" in error_str:
            click.echo("💡 Hint: Make sure you're in a valid git repository")
            
        ctx.exit(1)

def _handle_pr_update(ctx, dry_run):
    """
    Handles `bl pr update` command execution.
    
    Args:
        ctx: Click context for error handling
        dry_run: boolean flag for testing mode
    
    TODO: Implement update functionality
    - Find existing PR for current branch
    - Update title/body based on new changes
    - Push additional commits if needed
    """
    if dry_run:
        click.echo("🔍 DRY RUN: Would update existing PR (no actual changes)")
        return
        
    # TODO: Implement PR update logic
    click.secho("⚠️  PR update functionality coming soon!", fg="yellow")
    click.echo("For now, use 'bl pr create' to create a new PR.")
    ctx.exit(1)

# =============================================================================
# FUTURE SUBCOMMANDS
# =============================================================================

# To add a new top-level command like `bl status`:
#
# @cli.command(help="Show status of current branch and PRs")
# @click.pass_context
# def status(ctx):
#     """Handle `bl status` command"""
#     try:
#         # Your status logic here
#         pass
#     except Exception as e:
#         click.secho(f"❌ Failed to get status: {e}", fg="red", err=True)
#         ctx.exit(1)

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

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
        click.echo("\n⚠️  Operation cancelled by user", err=True)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        # Catch-all for truly unexpected errors (should be rare)
        click.secho(f"❌ Unexpected system error: {e}", fg="red", err=True)
        click.echo("This is likely a bug. Please report it to the team.")
        sys.exit(3)  # Exit code 3 = unexpected system error

# Allow running this file directly for testing
if __name__ == "__main__":
    main()