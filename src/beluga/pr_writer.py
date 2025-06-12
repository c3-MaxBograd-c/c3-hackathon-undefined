from narwhal.git_utils import get_repo, get_changed_files
from narwhal.ai_agent import draft_pr_with_ai

def create_pr():
    repo = get_repo()
    files = get_changed_files(repo)
    # TODO: gather diffs, commit msgs
    title, body = draft_pr_with_ai(files)
    # TODO: use PyGithub to open a PR with `title` and `body`
    print("PR Title:", title)
    print("PR Body:", body)