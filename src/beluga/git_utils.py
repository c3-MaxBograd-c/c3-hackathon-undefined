# -------------------------------------------------------------------
# Git helper utilities
# -------------------------------------------------------------------
# What it does:
#   - Wraps GitPython for common repo introspection:
#       • get_repo() → Repo object for current path
#       • get_changed_files() → list of modified file paths
#
# What it invokes:
#   - git.Repo from GitPython
#
# Where to add changes:
#   - If you need diffs, commit history, branch info, add new functions below.
#
# What not to change:
#   - The existing function signatures—other modules depend on them.
#
import git

def get_repo(path="."):
    """
    Return a GitPython Repo object rooted at `path`.
    """
    return git.Repo(path)

def get_changed_files(repo=None):
    """
    Return a list of files changed in the working tree vs HEAD.
    """
    repo = repo or get_repo()
    diffs = repo.head.commit.diff(None)
    return [d.a_path for d in diffs]

# === To Extend ===
# def get_commit_messages(...):
#     …
# def get_diff_for_file(...):
#     …