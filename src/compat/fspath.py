import sys
import os
import pathlib


def fspath(path):
    if sys.version_info >= (3, 6):
        return os.fspath(path)
    if isinstance(path, str):
        return path
    elif isinstance(path, pathlib.Path):
        return str(path)
    else:
        raise TypeError('str or Path expected')
