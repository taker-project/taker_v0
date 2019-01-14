import os
from os import path
from pathlib import Path
from . import utils

'''
Important notice about paths in this module:

All relative paths in TaskRepository are calculated relative to the task
directory, NOT to the current directory! The exception is the constructor,
which considers relative paths as relative to the current directory.

Also, the paths use pathlib.Path class and are not stored in "raw" string
format.
'''

# TODO : Make the buildsystem work on Windows

internal_dir = '.taker'


class TaskRepository:
    def init_task(self):
        Path.mkdir(self.directory / internal_dir)

    def relpath(self, cur_path):
        if not cur_path.is_absolute():
            cur_path = utils.relpath(self.abspath(cur_path))
        return utils.relpath(cur_path, self.directory)

    def abspath(self, cur_path):
        if cur_path.is_absolute():
            return utils.abspath(cur_path)
        else:
            return utils.abspath(self.directory.joinpath(cur_path))

    def to_root_dir(self):
        os.chdir(str(self.directory))

    def __init__(self, directory=None):
        if directory is None:
            directory = Path.cwd()
        self.directory = utils.abspath(directory)


def find_task_dir(start_dir=None):
    if start_dir is None:
        start_dir = Path.cwd()
    if (start_dir / internal_dir).is_dir():
        return start_dir
    for cur_dir in utils.abspath(start_dir).parents:
        if (cur_dir / internal_dir).is_dir():
            return cur_dir
    raise FileNotFoundError('not in task directory')
