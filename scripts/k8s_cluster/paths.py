import os

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.dirname(PACKAGE_DIR)
REPO_ROOT = os.path.dirname(SCRIPT_DIR)


def resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(SCRIPT_DIR, path))
