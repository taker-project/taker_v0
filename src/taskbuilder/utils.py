from os import path
from pathlib import Path
from compat import fspath


def abspath(cur_path):
    return Path(path.abspath(fspath(cur_path)))


def relpath(cur_path, start=None):
    if start is None:
        start = Path.cwd()
    return Path(path.relpath(fspath(cur_path), fspath(start)))
