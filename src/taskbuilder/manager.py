import os
import subprocess
from compat import fspath
from .repository import TaskRepository, get_repository
from .makefiles import Makefile
from .config import config


class TaskManager:
    @property
    def task_dir(self):
        return self.repo.directory

    def __init__(self, repo=None, task_dir=None, search_dir=None):
        if repo is None:
            if task_dir is None:
                repo = get_repository(search_dir)
            else:
                repo = TaskRepository(task_dir)
        self.repo = repo
        self.makefile = Makefile(repo)
        self.makefile.default_rule.add_depend('all')
        if not self.repo.is_task_dir():
            self.repo.init_task()

    def build(self, target=None):
        self.makefile.save()
        jobs = config()['make']['jobs']
        if jobs is None:
            jobs = os.cpu_count()
        args = ['make', '-j', str(jobs)]
        if target is not None:
            args += [target]
        subprocess.check_call(args, cwd=fspath(self.repo.directory))
