# -------------------------------------------------------------------
# PR Writer / Orchestrator
# -------------------------------------------------------------------
# What it does:
#   - Orchestrates gathering diffs + AI generation + GitHub PR creation.
#
# What it invokes:
#   - get_repo(), get_changed_files() from git_utils
#   - draft_pr_with_ai() from ai_agent
#   - (future) PyGithub to create PR on GitHub
#
# Where to add changes:
#   - Under TODO markers:
#       • Collect commit messages or diffs
#       • Authenticate with GitHub and open the PR
#
# What not to change:
#   - Function name `create_pr()` as CLI expects it.
#
from beluga.git_utils import get_repo, get_changed_files
from beluga.ai_agent import draft_pr_with_ai

def create_pr():
    """
    Main function called by `bl pr create`.
    1) Reads repo and changed files
    2) Calls AI to draft title/body
    3) Opens a GitHub pull request
    """
    repo = get_repo()
    files = get_changed_files(repo)

    # TODO: Read diffs and commit messages:
    # diffs = [repo.git.diff(f) for f in files]

    # Call AI agent to produce (title, body)
    title, body = draft_pr_with_ai(files)

    # TODO: Use PyGithub:
    # from github import Github
    # gh = Github(os.environ["GITHUB_TOKEN"])
    # repo = gh.get_repo(repo.remote().url)
    # repo.create_pull(title=title, body=body, head=…, base=…)

    # For now, print to STDOUT
    print("PR Title:", title)
    print("PR Body:", body)