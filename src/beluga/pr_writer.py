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
#   - Function name `generate_pr_content()` as CLI dry-run expects it.
#
from beluga.git_utils import get_repo, get_changed_files
from beluga.ai_agent import draft_pr_with_ai

def create_pr(title=None, body=None):
    """
    Main function called by `bl pr create`.
    
    Args:
        title: Optional pre-generated title (from dry-run mode)
        body: Optional pre-generated body (from dry-run mode)
    
    Flow:
    1) If title/body provided (dry-run mode), use them directly
    2) Otherwise, read repo and changed files
    3) Call AI to draft title/body if not provided
    4) Open a GitHub pull request
    
    Returns:
        str: URL of created PR, or None if just printing
    """
    if title and body:
        # Use provided title/body (from dry-run mode)
        print("Creating PR with provided content...")
        print("PR Title:", title)
        print("PR Body:", body)
        
        # TODO: Use PyGithub to create PR with provided content:
        # from github import Github
        # gh = Github(os.environ["GITHUB_TOKEN"])
        # repo_obj = gh.get_repo(repo.remote().url)
        # pr = repo_obj.create_pull(title=title, body=body, head=…, base=…)
        # return pr.html_url
        
        return None  # For now, just return None
    else:
        # Generate content normally
        repo = get_repo()
        files = get_changed_files(repo)

        # TODO: Read diffs and commit messages:
        # diffs = [repo.git.diff(f) for f in files]

        # Call AI agent to produce (title, body)
        title, body = draft_pr_with_ai(files)

        # TODO: Use PyGithub:
        # from github import Github
        # gh = Github(os.environ["GITHUB_TOKEN"])
        # repo_obj = gh.get_repo(repo.remote().url)
        # pr = repo_obj.create_pull(title=title, body=body, head=…, base=…)
        # return pr.html_url

        # For now, print to STDOUT
        print("PR Title:", title)
        print("PR Body:", body)
        return None

def generate_pr_content():
    """
    Generate PR title and body without creating the actual PR.
    Used for dry-run mode.
    
    Flow:
    1) Read repo and changed files
    2) Call AI to draft title/body
    3) Return content without creating PR
    
    Returns:
        tuple: (title, body) strings
    """
    repo = get_repo()
    files = get_changed_files(repo)

    # TODO: Read diffs and commit messages:
    # diffs = [repo.git.diff(f) for f in files]

    # Call AI agent to produce (title, body)
    title, body = draft_pr_with_ai(files)
    
    return title, body

def update_pr():
    """
    Main function called by `bl pr update`.
    
    TODO: Implement update functionality:
    - Find existing PR for current branch
    - Update title/body based on new changes
    - Push additional commits if needed
    
    Returns:
        str: URL of updated PR or raises on failure
    """
    # TODO: Implement PR update logic
    raise NotImplementedError("update_pr() not yet implemented")