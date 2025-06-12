import git

def get_repo(path="."):
    return git.Repo(path)

def get_changed_files(repo=None):
    repo = repo or get_repo()
    return [diff.a_path for diff in repo.head.commit.diff(None)]

# you can expand with diffs, commit messages, etc.