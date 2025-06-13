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
#   - `bl pr create --dry-run` → generates PR content, shows preview, asks for confirmation
#   - `bl pr update` → calls update_pr() in pr_writer.py (TODO)
#   - `bl pr` (no action) → shows available pr actions
#   - You can add new commands by decorating functions with @cli.command()
#
# Where to extend:
#   - For new PR actions, add elif branches in pr_cmd()
#   - For new top-level commands, add @cli.command() decorators below pr_cmd
#   - Update valid_actions list when adding new PR actions
#
# What not to change:
#   - The @click.group() decorator and the entry-point definition
#     `bl = "beluga.cli:cli"` in pyproject.toml.
#   - The main() function signature (console_scripts expects it)
# -------------------------------------------------------------------

import sys
import click

from beluga.src.pr_writer import create_pr, generate_pr_content, update_pr
from beluga.src import messages

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
    help=messages.PR_HELP,
    context_settings={"allow_extra_args": False, "allow_interspersed_args": False}
)
@click.argument("action", required=False, metavar="[create|update]")
@click.option(
    "--dry-run",
    is_flag=True,
    help=messages.DRY_RUN_HELP
)
@click.pass_context
def pr_cmd(ctx, action, dry_run):
    """
    Handles all `bl pr <action>` commands.
    
    Input validation:
    - action: optional string, if not provided shows available actions
    - dry_run: optional flag for testing without side effects
    
    Behavior:
    - no action: shows available PR actions and exits
    - "create": calls create_pr() or interactive dry-run mode
    - "update": (future) calls update_pr() 
    - unknown action: shows error + help, exits with code 2
    - any exception from pr_writer: shows error, exits with code 1
    
    Exit codes:
    - 0: success or showed help
    - 1: PR operation failed (network, auth, validation, etc.)
    - 2: invalid user input (unknown action)
    """
    
    # If no action provided, show available actions (like --help but custom)
    if action is None or action.strip() == "":
        click.echo(messages.PR_NO_ACTION_HELP)
        ctx.exit(0)  # Exit successfully after showing help
    
    # Input normalization and validation
    action = action.lower().strip()  # normalize user input
    
    # Validate action is supported
    valid_actions = ["create", "update"]
    if action not in valid_actions:
        click.secho(
            messages.ERR_UNKNOWN_ACTION.format(action=action),
            fg="yellow",
            err=True
        )
        click.echo(messages.HELP_VALID_ACTIONS.format(actions=", ".join(valid_actions)))
        click.echo(f"\n{messages.HELP_MORE_INFO}")
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
        dry_run: boolean flag for preview mode
    
    Behavior:
    - Normal mode: Creates PR directly
    - Dry-run mode: Shows AI-generated content, asks for user confirmation/edits
    """
    try:
        if dry_run:
            _handle_dry_run_create(ctx)
        else:
            # Normal create flow
            click.echo(messages.LOG_CREATING_PR)
            result = create_pr()  # Should return URL or success info
            
            # Handle success
            if result:
                click.secho(messages.SUCCESS_PR_CREATED.format(result=result), fg="green")
            else:
                click.secho(messages.SUCCESS_PR_CREATED_SIMPLE, fg="green")
                
    except FileNotFoundError as e:
        click.secho(messages.ERR_FILE_NOT_FOUND.format(error=e), fg="red", err=True)
        click.echo(messages.HELP_FILE_NOT_FOUND)
        ctx.exit(1)
        
    except PermissionError as e:
        click.secho(messages.ERR_PERMISSION_DENIED.format(error=e), fg="red", err=True)
        click.echo(messages.HELP_PERMISSION_DENIED)
        ctx.exit(1)
        
    except Exception as e:
        click.secho(
            messages.ERR_PR_FAILURE.format(error=str(e)),
            fg="red",
            err=True
        )
        
        # Provide helpful context based on error type
        error_str = str(e).lower()
        if "authentication" in error_str or "token" in error_str:
            click.echo(messages.HINT_CHECK_TOKEN)
        elif "network" in error_str or "connection" in error_str:
            click.echo(messages.HINT_CHECK_NETWORK)
        elif "git" in error_str:
            click.echo(messages.HINT_CHECK_GIT_REPO)
            
        ctx.exit(1)

def _handle_dry_run_create(ctx):
    """
    Handles dry-run mode for PR creation.
    
    Flow:
    1. Generate AI content (title + body)
    2. Display preview to user
    3. Ask user: create, edit, or discard
    4. Handle user choice accordingly
    """
    click.echo(messages.LOG_DRY_RUN_CREATE)
    click.echo(messages.LOG_GENERATING_AI)
    
    try:
        # Generate PR content using AI (without creating actual PR)
        title, body = generate_pr_content()  # New function in pr_writer.py
        
        # Display the preview
        _display_pr_preview(title, body)
        
        # Interactive loop for user choice
        while True:
            choice = click.prompt(messages.PROMPT_DRY_RUN_ACTION, type=str).lower().strip()
            
            if choice == 'c':
                # Create PR with current content
                click.echo(messages.LOG_CREATING_PR)
                result = create_pr(title=title, body=body)  # Pass generated content
                if result:
                    click.secho(messages.SUCCESS_PR_CREATED.format(result=result), fg="green")
                else:
                    click.secho(messages.SUCCESS_PR_CREATED_SIMPLE, fg="green")
                break
                
            elif choice == 'e':
                # Edit title and body
                title, body = _edit_pr_content(title, body)
                _display_pr_preview(title, body)
                
                # Ask for final confirmation
                if click.confirm(messages.PROMPT_CONFIRM_EDIT):
                    click.echo(messages.LOG_CREATING_PR)
                    result = create_pr(title=title, body=body)
                    if result:
                        click.secho(messages.SUCCESS_PR_CREATED.format(result=result), fg="green")
                    else:
                        click.secho(messages.SUCCESS_PR_CREATED_SIMPLE, fg="green")
                    break
                # If not confirmed, continue the loop to show options again
                
            elif choice == 'd':
                # Discard and exit
                click.secho(messages.SUCCESS_DRY_RUN_DISCARDED, fg="yellow")
                ctx.exit(0)
                
            else:
                # Invalid choice
                click.secho(messages.ERR_INVALID_CHOICE, fg="red", err=True)
                # Continue loop to ask again
                
    except Exception as e:
        # Handle errors in dry-run mode
        click.secho(messages.ERR_PR_FAILURE.format(error=str(e)), fg="red", err=True)
        ctx.exit(1)

def _display_pr_preview(title, body):
    """
    Display the AI-generated PR content in a nice format.
    
    Args:
        title: PR title string
        body: PR body/description string
    """
    click.echo(f"\n{messages.DRY_RUN_SEPARATOR}")
    click.secho(messages.DRY_RUN_HEADER, fg="cyan", bold=True)
    click.echo(messages.DRY_RUN_SEPARATOR)
    
    click.secho(f"\n{messages.DRY_RUN_TITLE_LABEL}", fg="blue", bold=True)
    click.echo(title)
    
    click.secho(f"\n{messages.DRY_RUN_BODY_LABEL}", fg="blue", bold=True)
    click.echo(body)
    
    click.echo(f"\n{messages.DRY_RUN_SEPARATOR}")

def _edit_pr_content(current_title, current_body):
    """
    Allow user to edit PR title and body interactively.
    
    Args:
        current_title: existing title string
        current_body: existing body string
        
    Returns:
        tuple: (new_title, new_body)
    """
    click.echo(f"\nCurrent title: {current_title}")
    new_title = click.prompt(messages.PROMPT_EDIT_TITLE, default="", show_default=False)
    if new_title.strip():
        current_title = new_title.strip()
    
    click.echo(f"\nCurrent description:\n{current_body}")
    new_body = click.prompt(messages.PROMPT_EDIT_BODY, default="", show_default=False)
    if new_body.strip():
        current_body = new_body.strip()
    
    return current_title, current_body

def _handle_pr_update(ctx, dry_run):
    """
    Handles `bl pr update` command execution.
    
    Args:
        ctx: Click context for error handling
        dry_run: boolean flag for testing mode
    
    Behavior:
    - Finds existing PR for current branch
    - Updates title/body with new content
    - If no PR exists, tells user to create one first
    """
    try:
        if dry_run:
            click.echo(messages.LOG_DRY_RUN_UPDATE)
            return
        
        # Call the actual update function
        click.echo("🔄 Updating existing PR...")
        result = update_pr()
        
        # Handle results
        if result:
            click.secho(f"✅ PR updated successfully: {result}", fg="green")
        else:
            click.secho("ℹ️  No PR found to update", fg="yellow")
            click.echo("💡 Create a PR first by running: bl pr create")
            
    except FileNotFoundError as e:
        click.secho(f"❌ File not found: {e}", fg="red", err=True)
        ctx.exit(1)
        
    except PermissionError as e:
        click.secho(f"❌ Permission denied: {e}", fg="red", err=True)
        ctx.exit(1)
        
    except Exception as e:
        click.secho(f"❌ Failed to update PR: {e}", fg="red", err=True)
        
        # Provide helpful context based on error type
        error_str = str(e).lower()
        if "authentication" in error_str or "token" in error_str:
            click.echo("💡 Check your GITHUB_TOKEN environment variable")
        elif "network" in error_str or "connection" in error_str:
            click.echo("💡 Check your internet connection")
        elif "git" in error_str:
            click.echo("💡 Make sure you're in a git repository")
            
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