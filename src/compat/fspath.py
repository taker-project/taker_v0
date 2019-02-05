import sys
import os
import pathlib


def fspath(path):
    if sys.version_info >= (3, 6):
        return os.fspath(path)
    if isinstance(path, str):
        return path
    if isinstance(path, pathlib.Path):
        return str(path)
    if hasattr(path, '__fspath__'):
        return path.__fspath__()
    raise TypeError('str or PathLike expected')
