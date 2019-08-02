from os import path
from pathlib import Path


def tests_location():
    return Path(path.abspath(path.join('src', 'invoker', 'tests')))
