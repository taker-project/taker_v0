from taskbuilder import RepositoryManager, TaskDirNotFoundError
from invoker import LanguageManager
from cli import ConsoleApp, app


class GlobalState:
    @property
    def repo(self):
        return self.repo_manager.repo

    def __init__(self, task_dir=None):
        self.repo_manager = RepositoryManager(task_dir=task_dir)
        self.lang_manager = LanguageManager(self.repo_manager)
