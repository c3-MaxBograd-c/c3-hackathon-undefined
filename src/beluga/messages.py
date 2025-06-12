# -----------------------------------------------------------------------------
# Central place for all terminal‐visible text.
# New developers: add prompts/errors here.
# -----------------------------------------------------------------------------

# CLI description
CLI_DESC            = "Beluga (bl) — Agentic AI PR creator."

# pr subcommand help
PR_HELP             = "Generate or manage pull requests."
PR_ACTION_HELP      = "Valid actions: create"
PR_CREATE_DESC      = "Draft a PR using our AI agent."

# Status messages
LOG_FETCHING_DIFFS  = "⏳ Fetching diffs for changed files…"
LOG_CALLING_AI      = "🤖 Calling AI to draft your PR…"

# Success / Error
SUCCESS_PR_CREATED  = "✅ PR created successfully: {url}"
ERR_PR_FAILURE      = "❌ Failed to create PR: {error}"
ERR_UNKNOWN_ACTION  = "❌ Unknown PR action: {action!r}"