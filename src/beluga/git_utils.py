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
    Return a list of files changed (with their diffs) between the most recent commit
    on the current branch and the 'develop' branch.
    Returns a list of dicts: [{'path': <file>, 'diff': <diff_text>}]
    """
    repo = repo or get_repo()
    # Get the current branch's latest commit
    head_commit = repo.head.commit
    # Get the latest commit on 'develop'
    develop_commit = repo.merge_base(head_commit, 'develop')[0]
    # Get the diff between develop and HEAD
    diffs = head_commit.diff(develop_commit, create_patch=True)
    changed = []
    for d in diffs:
        # d.a_path is the file path, d.diff is the patch text (bytes)
        changed.append({
            'path': d.a_path,
            'diff': d.diff.decode('utf-8', errors='replace') if d.diff else ''
        })
    return changed

# === To Extend ===
# def get_commit_messages(...):
#     …
# def get_diff_for_file(...):
#     …