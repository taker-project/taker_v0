from os import path
from pathlib import Path


def abspath(cur_path):
    return Path(path.abspath(str(cur_path)))


def relpath(cur_path, start=None):
    if start is None:
        start = Path.cwd()
    return Path(path.relpath(str(cur_path), str(start)))
