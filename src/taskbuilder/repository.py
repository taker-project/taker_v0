'''
Base task directory management

Important notice about paths in this module:

All relative paths in TaskRepository are calculated relative to the task
directory, NOT to the current directory! The exception is the constructor,
which considers relative paths as relative to the current directory.

Also, the paths use pathlib.Path class and are not stored in "raw" string
format.
'''
import os
from pathlib import Path
from compat import fspath
from taskbuilder import utils

# TODO : Make the buildsystem work on Windows

INTERNAL_DIR = '.taker'
INTERNAL_PATH = Path(INTERNAL_DIR)


class TaskDirNotFoundError(Exception):
    pass


class TaskRepository:
    @staticmethod
    def check_task_dir(directory):
        return (Path(directory) / INTERNAL_DIR).is_dir()

    def is_task_dir(self):
        return TaskRepository.check_task_dir(self.directory)

    def init_task(self):
        self.mkdir(INTERNAL_PATH)

    def internal_dir(self, absolute=False):
        return self.abspath(INTERNAL_DIR) if absolute else INTERNAL_DIR

    def relpath(self, cur_path):
        cur_path = Path(cur_path)
        if not cur_path.is_absolute():
            cur_path = self.abspath(cur_path)
        return utils.relpath(cur_path, self.directory)

    def abspath(self, cur_path):
        cur_path = Path(cur_path)
        if cur_path.is_absolute():
            return utils.abspath(cur_path)
        return utils.abspath(self.directory.joinpath(cur_path))

    def mkdir(self, location, *args, **kwargs):
        self.abspath(location).mkdir(*args, **kwargs)

    def to_task_dir(self):
        os.chdir(fspath(self.directory))

    def open(self, filename, *args, encoding='utf8', **kwargs):
        return self.abspath(filename).open(*args, encoding=encoding, **kwargs)

    def __init__(self, directory=None):
        if directory is None:
            directory = Path.cwd()
        self.directory = utils.abspath(directory)


def find_task_dir(start_dir=None):
    if start_dir is None:
        start_dir = Path.cwd()
    if TaskRepository.check_task_dir(start_dir):
        return start_dir
    for cur_dir in utils.abspath(start_dir).parents:
        if TaskRepository.check_task_dir(cur_dir):
            return cur_dir
    raise TaskDirNotFoundError('not in task directory')


def get_repository(start_dir=None):
    return TaskRepository(find_task_dir(start_dir))
