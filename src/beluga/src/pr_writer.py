# -------------------------------------------------------------------
# PR Writer / Orchestrator
# -------------------------------------------------------------------
# What it does:
#   - Orchestrates gathering diffs + AI generation + GitHub PR creation.
#
# What it invokes:
#   - get_repo(), get_changed_files() from git_utils
#   - draft_pr_with_ai() from ai_agent
#   - PyGithub to create PR on GitHub
#
# Where to add changes:
#   - Under TODO markers:
#       • Collect commit messages or diffs
#
# What not to change:
#   - Function name `create_pr()` as CLI expects it.
#   - Function name `generate_pr_content()` as CLI dry-run expects it.
#

import os
from typing import Optional, Tuple
from urllib.parse import urlparse
from beluga.src.git_utils import get_repo, get_changed_files
from beluga.src.ai_agent import draft_pr_with_ai
import beluga.src.jira_utils as jira_utils
from dotenv import load_dotenv

def create_pr(title: Optional[str] = None, body: Optional[str] = None) -> Optional[str]:
    """
    Main function called by `bl pr create`.
    
    Args:
        title: Optional pre-generated title (from dry-run mode)
        body: Optional pre-generated body (from dry-run mode)
    
    Flow:
    1) If title/body provided (dry-run mode), use them directly
    2) Otherwise, read repo and changed files
    3) Call AI to draft title/body if not provided
    4) Get current branch and remote info
    5) Open a GitHub pull request
    
    Returns:
        str: URL of created PR, or None if just printing for now
        
    Raises:
        Exception: If git repo issues, GitHub auth issues, or API errors
    """
    try:
        # Setup GitHub connection and get repo info
        setup_result = _setup_github_connection()
        if not setup_result:
            return 'Please set GITHUB_TOKEN in your environment to create a PR.'
        
        repo, current_branch, owner, repo_name, github_repo, base_branch = setup_result
        
        if title and body:
            # Use provided title/body (from dry-run mode)
            print("✅ Using provided PR content...")
        else:
            # Generate content normally
            files = get_changed_files(repo)

            file_paths = [file['path'] for file in files]
            print(f"📝 Found {len(files)} changed files:")
            print('\n'.join(f"\t{file_path}" for file_path in file_paths))            
            # TODO: Read diffs and commit messages for more context:
            # diffs = []
            # for file_path in files:
            #     try:
            #         diff = repo.git.diff('HEAD', file_path)
            #         diffs.append({'file': file_path, 'diff': diff})
            #     except Exception as e:
            #         print(f"⚠️  Could not get diff for {file_path}: {e}")
            jiraFetch = fetch_jira_info_from_branch()
            jira_data = jira_utils.get_jira_ticket_info(jiraFetch)
            print("🤖 Generating PR content with AI...")
            # Call AI agent to produce (title, body)
            title, body = draft_pr_with_ai(files, jira_data, template)
        
        # Validate we have content
        if not title or not body:
            raise ValueError("AI failed to generate PR title or body")
            
        print("\n" + "="*60)
        print("📋 Generated PR Content:")
        print("="*60)
        print(f"Title: {title}")
        print(f"\nBody:\n{body}")
        print("="*60)
        
        # Check if current branch exists on remote
        try:
            from github.GithubException import GithubException
            github_repo.get_branch(current_branch)
            print(f"✅ Branch '{current_branch}' found on remote")
        except GithubException as e:
            if e.status == 404:
                raise Exception(
                    f"Branch '{current_branch}' not found on remote. "
                    f"Push your branch first: git push -u origin {current_branch}"
                )
            else:
                raise Exception(f"Error checking branch: {e}")
        
        # Check if PR already exists
        existing_prs = github_repo.get_pulls(
            state='open',
            head=f"{owner}:{current_branch}",
            base=base_branch
        )
        
        if existing_prs.totalCount > 0:
            existing_pr = existing_prs[0]
            print(f"⚠️  PR already exists for branch '{current_branch}'")
            print(f"🔗 Existing PR: {existing_pr.html_url}")
            
            # Ask if user wants to update existing PR
            # For now, just return the existing PR URL
            return existing_pr.html_url
        
        # Create the PR
        print("🚀 Creating pull request...")
        pr = github_repo.create_pull(
            title=title,
            body=body,
            head=current_branch,
            base=base_branch,
            draft=False  # Set to True if you want draft PRs by default
        )
        
        print(f"✅ PR created successfully!")
        print(f"🔗 PR URL: {pr.html_url}")
        print(f"📊 PR #{pr.number}: {pr.title}")
        
        return pr.html_url
        
    except Exception as e:
        print(f"❌ Error in create_pr(): {e}")
        raise

def generate_pr_content() -> Tuple[str, str]:
    """
    Generate PR title and body without creating the actual PR.
    Used for dry-run mode.
    
    Flow:
    1) Read repo and changed files
    2) Call AI to draft title/body
    3) Return content without creating PR
    
    Returns:
        tuple: (title, body) strings
        
    Raises:
        Exception: If git repo issues or AI generation fails
    """
    try:
        repo = get_repo()
        files = get_changed_files(repo)
        
        print(f"📝 Analyzing {len(files)} changed files...")
        
        # TODO: Read diffs and commit messages for more context:
        # diffs = []
        # for file_path in files:
        #     try:
        #         diff = repo.git.diff('HEAD', file_path)
        #         diffs.append({'file': file_path, 'diff': diff})
        #     except Exception as e:
        #         print(f"⚠️  Could not get diff for {file_path}: {e}")

        print("🤖 Generating PR content...")
        # Call AI agent to produce (title, body)
        title, body = draft_pr_with_ai(files)
        
        if not title or not body:
            raise ValueError("AI failed to generate PR title or body")
            
        return title, body
        
    except Exception as e:
        print(f"❌ Error in generate_pr_content(): {e}")
        raise

def update_pr() -> Optional[str]:
    """
    Main function called by `bl pr update`.
    
    Flow:
    1) Get repository and current branch info
    2) Find existing PR for current branch
    3) If no PR exists, tell user to create one
    4) If PR exists, update it with new content
    
    Returns:
        str: URL of updated PR or None if no PR found
        
    Raises:
        Exception: If git repo issues, GitHub auth issues, or API errors
    """
    try:
        # Setup GitHub connection and get repo info
        setup_result = _setup_github_connection()
        if not setup_result:
            return None
        
        repo, current_branch, owner, repo_name, github_repo, base_branch = setup_result
        
        # Look for existing PR for current branch
        print(f"🔍 Looking for existing PR for branch '{current_branch}'...")
        existing_prs = github_repo.get_pulls(
            state='open',
            head=f"{owner}:{current_branch}",
            base=base_branch
        )
        
        if existing_prs.totalCount == 0:
            print(f"❌ No open PR found for branch '{current_branch}'")
            print("💡 Create a PR first by running: bl pr create")
            return None
        
        # Get the existing PR
        existing_pr = existing_prs[0]
        print(f"✅ Found existing PR #{existing_pr.number}: {existing_pr.title}")
        print(f"🔗 Current PR: {existing_pr.html_url}")
        
        # Update the PR with hardcoded message for now
        print("📝 Updating PR with new content...")
        
        # For now, just append "edited" to the body as requested
        current_body = existing_pr.body or ""

        # call the generate content with ai function but with prompt to update the PR
        # prompt should be telling the ai to consider what we already have in the PR and keep most of it
        # edit the pr in a way to include new changes that are not included in the current PR body
        # For now, just append "edited" to the body
        updated_body = current_body + "\n\n---\n**Updated:** edited"
        
        # Update the PR
        existing_pr.edit(body=updated_body)
        
        print(f"✅ PR updated successfully!")
        print(f"🔗 Updated PR: {existing_pr.html_url}")
        
        return existing_pr.html_url
        
    except Exception as e:
        print(f"❌ Error in update_pr(): {e}")
        raise

def _get_remote_url(repo) -> str:
    """
    Get the remote URL for the repository.
    
    Args:
        repo: GitPython repo object
        
    Returns:
        str: Remote URL
        
    Raises:
        Exception: If no remote found
    """
    try:
        # Try 'origin' remote first
        if 'origin' in repo.remotes:
            return repo.remotes.origin.url
        
        # If no origin, use the first remote
        if repo.remotes:
            return repo.remotes[0].url
            
        raise Exception("No git remote found")
        
    except Exception as e:
        raise Exception(f"Could not get remote URL: {e}")

def _parse_github_url(url: str) -> Tuple[str, str]:
    """
    Parse GitHub URL to extract owner and repository name.
    
    Args:
        url: Git remote URL (HTTPS or SSH)
        
    Returns:
        tuple: (owner, repo_name)
        
    Examples:
        'https://github.com/owner/repo.git' -> ('owner', 'repo')
        'git@github.com:owner/repo.git' -> ('owner', 'repo')
    """
    try:
        # Handle SSH format: git@github.com:owner/repo.git
        if url.startswith('git@'):
            # Extract the part after the colon
            path_part = url.split(':')[1]
            # Remove .git suffix if present
            if path_part.endswith('.git'):
                path_part = path_part[:-4]
            owner, repo_name = path_part.split('/')
            return owner, repo_name
        
        # Handle HTTPS format: https://github.com/owner/repo.git
        parsed = urlparse(url)
        if 'github.com' not in parsed.netloc:
            raise ValueError("Not a GitHub URL")
            
        # Extract path and remove leading slash
        path = parsed.path.lstrip('/')
        
        # Remove .git suffix if present
        if path.endswith('.git'):
            path = path[:-4]
            
        # Split into owner and repo
        parts = path.split('/')
        if len(parts) != 2:
            raise ValueError("Invalid GitHub URL format")
            
        return parts[0], parts[1]
        
    except Exception as e:
        raise Exception(f"Could not parse GitHub URL '{url}': {e}")

def _get_base_branch(github_repo) -> str:
    """
    Determine the base branch for the PR (usually 'main' or 'master').
    
    Args:
        github_repo: PyGithub repository object
        
    Returns:
        str: Base branch name
    """
    try:
        # Get the default branch
        return github_repo.default_branch
    except Exception:
        # Fallback to common branch names
        for branch_name in ['main', 'master', 'develop']:
            try:
                github_repo.get_branch(branch_name)
                return branch_name
            except:
                continue
        
        # If all else fails, use 'main'
        return 'main'

def _setup_github_connection():
    """
    Setup GitHub connection and repository information.
    
    Returns:
        tuple: (repo, current_branch, owner, repo_name, github_repo, base_branch) or None if setup fails
        
    Raises:
        Exception: If setup fails at any step
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Get repository and basic info
        repo = get_repo()
        current_branch = repo.active_branch.name
        
        # Get remote repository info
        remote_url = _get_remote_url(repo)
        owner, repo_name = _parse_github_url(remote_url)
        
        print(f"📁 Repository: {owner}/{repo_name}")
        print(f"🌿 Current branch: {current_branch}")
        
        # Check for GitHub token
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            print("❌ Error: GITHUB_TOKEN not found in environment")
            print("💡 Set GITHUB_TOKEN to enable GitHub operations")
            return None
        
        # Setup GitHub connection
        try:
            from github import Github
            from github.GithubException import GithubException
            
            print("🔐 Authenticating with GitHub...")
            gh = Github(github_token)
            
            # Test authentication
            user = gh.get_user()
            print(f"✅ Authenticated as: {user.login}")
            
            # Get the repository
            print(f"📡 Accessing repository {owner}/{repo_name}...")
            github_repo = gh.get_repo(f"{owner}/{repo_name}")
            
            # Determine base branch (usually 'main' or 'master')
            base_branch = _get_base_branch(github_repo)
            print(f"🎯 Base branch: {base_branch}")
            
            return repo, current_branch, owner, repo_name, github_repo, base_branch
            
        except ImportError:
            print("❌ PyGithub not installed. Install with: pip install PyGithub")
            return None
            
        except Exception as e:
            from github.GithubException import GithubException
            if isinstance(e, GithubException):
                if e.status == 401:
                    raise Exception("GitHub authentication failed. Check your GITHUB_TOKEN.")
                elif e.status == 403:
                    raise Exception("GitHub access forbidden. Check your token permissions.")
                elif e.status == 404:
                    raise Exception(f"Repository {owner}/{repo_name} not found or no access.")
                else:
                    raise Exception(f"GitHub API error: {e}")
            else:
                raise Exception(f"Failed to setup GitHub connection: {e}")
        
    except Exception as e:
        print(f"❌ Error in _setup_github_connection(): {e}")
        raise

def fetch_jira_info_from_branch():
    
    branchName = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
    
    
    ticketName = branch_name.split('/')[-1]
    
    if not ticket_name:
         raise ValueError("Ticket name could not be extracted from branch name.")
    
    jiraInfo = get_jira_ticket_info(ticket_name)
    
    return jiraInfo
