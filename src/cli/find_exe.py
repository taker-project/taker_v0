import os
import shutil
import sys
from pathlib import Path
from .consoleapp import app


def __find_app_exe(name):
    res = shutil.which(sys.argv[0])
    if (res is not None) and (Path(res).stem == name):
        return res
    res = shutil.which(name)
    if res is not None:
        return res
    return None


def app_exe(name=None):
    if name is None:
        name = app().name
    res = __find_app_exe(name)
    if res is None:
        raise RuntimeError('could not find "{}" execuable'.format(name))
    return Path(res)
