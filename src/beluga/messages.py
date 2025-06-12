# -----------------------------------------------------------------------------
# Central place for all terminal‐visible text.
# New developers: add prompts/errors here.
# -----------------------------------------------------------------------------

# CLI description
CLI_DESC            = """Beluga (bl) — Agentic AI PR creator.

Commands:
  pr      Generate or manage pull requests

Examples:
  bl pr create              Create a new pull request
  bl pr create --dry-run    Preview PR content before creating
  bl pr update              Update existing pull request
  bl pr                     Show available PR actions

Run 'bl <command> --help' for more details on each command."""

# pr subcommand help
PR_HELP             = "Generate or manage pull requests."
PR_NO_ACTION_HELP   = """Usage: bl pr <action> [options]

Available actions:
  create    Draft a new PR using our AI agent
  update    Update an existing PR with your latest changes

Options:
  --dry-run    Preview PR content without creating it

Examples:
  bl pr create              Create a new pull request
  bl pr create --dry-run    Preview PR content before creating
  bl pr update              Update existing pull request

Run 'bl pr <action> --help' for more details on each action."""

PR_ACTION_HELP      = "Valid actions: {actions}"
PR_CREATE_DESC      = "Draft a new PR using our AI agent."
PR_UPDATE_DESC      = "Update an existing PR with your latest changes."

# Status messages
LOG_CREATING_PR     = "🚀 Creating new PR..."
LOG_DRY_RUN_CREATE  = "🔍 DRY RUN: Generating PR content preview..."
LOG_DRY_RUN_UPDATE  = "🔍 DRY RUN: Would update existing PR (no actual changes)"
LOG_GENERATING_AI   = "🤖 AI is analyzing your changes..."

# Dry run output
DRY_RUN_SEPARATOR   = "=" * 60
DRY_RUN_HEADER      = "📋 PREVIEW: AI-Generated PR Content"
DRY_RUN_TITLE_LABEL = "Title:"
DRY_RUN_BODY_LABEL  = "Description:"

# Dry run prompts
PROMPT_DRY_RUN_ACTION = """
What would you like to do?
  [c] Create this PR as-is
  [e] Edit the title/description  
  [d] Discard and exit

Choice (c/e/d): """

PROMPT_EDIT_TITLE   = "Enter new title (or press Enter to keep current): "
PROMPT_EDIT_BODY    = "Enter new description (or press Enter to keep current): "
PROMPT_CONFIRM_EDIT = "Create PR with these changes? [y/N]: "

# Success messages
SUCCESS_PR_CREATED       = "✅ PR created successfully: {result}"
SUCCESS_PR_CREATED_SIMPLE= "✅ PR created successfully"
SUCCESS_DRY_RUN_DISCARDED= "❌ PR creation cancelled"

# Error messages
ERR_PR_FAILURE           = "❌ Failed to create PR: {error}"
ERR_UNKNOWN_ACTION       = "❌ Unknown PR action: {action}"
ERR_FILE_NOT_FOUND       = "❌ File not found: {error}"
ERR_PERMISSION_DENIED    = "❌ Permission denied: {error}"
ERR_OPERATION_CANCELLED  = "⚠️  Operation cancelled by user"
ERR_UNEXPECTED_SYSTEM    = "❌ Unexpected system error: {error}"
ERR_INVALID_CHOICE       = "❌ Invalid choice. Please enter 'c', 'e', or 'd'."

# Help text
HELP_VALID_ACTIONS       = "Valid actions: {actions}"
HELP_MORE_INFO           = "Run 'bl pr --help' for more information."
HELP_FILE_NOT_FOUND      = "Make sure you're in a git repository with changes to commit."
HELP_PERMISSION_DENIED   = "Check your file permissions and git repository access."
HELP_BUG_REPORT          = "This is likely a bug. Please report it to the team."

# Hints
HINT_CHECK_TOKEN         = "💡 Hint: Check your GitHub token in the .env file"
HINT_CHECK_NETWORK       = "💡 Hint: Check your internet connection"
HINT_CHECK_GIT_REPO      = "💡 Hint: Make sure you're in a valid git repository"

# Feature status
FEATURE_UPDATE_COMING    = "⚠️  PR update functionality coming soon!"
FEATURE_UPDATE_WORKAROUND= "For now, use 'bl pr create' to create a new PR."

# Dry run flag help
DRY_RUN_HELP            = "Preview PR content without creating it (interactive mode)"