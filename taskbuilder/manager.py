import os
from os import path
from pathlib import Path

# TODO : Make the buildsystem work on Windows

internal_dir = '.taker'


class TaskManager:
    def init_task(self):
        Path.mkdir(self.directory / internal_dir)

    def relpath(self, cur_path):
        return Path(path.relpath(str(cur_path), start=str(self.directory)))

    def abspath(self, cur_path):
        if cur_path.is_absolute():
            return cur_path.resolve()
        else:
            return self.directory.joinpath(cur_path).resolve()

    def to_root_dir(self):
        os.chdir(str(self.directory))

    def __init__(self, directory=None):
        if directory is None:
            directory = Path.cwd()
        self.directory = directory.resolve()


def find_task_dir(start_dir=None):
    if start_dir is None:
        start_dir = Path.cwd()
    if (start_dir / internal_dir).is_dir():
        return start_dir
    for cur_dir in start_dir.resolve().parents:
        if (cur_dir / internal_dir).is_dir():
            return cur_dir
    raise FileNotFoundError('not in task directory')


task_manager = None


def manager():
    global task_manager
    if task_manager is None:
        task_manager = TaskManager(find_task_dir())
    return task_manager
