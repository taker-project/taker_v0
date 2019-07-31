from pathlib import Path
from copy import deepcopy
import pytest
import configs
from taskbuilder.manager import TaskManager
from invoker import LanguageManager


@pytest.fixture(scope='function')
def config_manager(tmpdir):
    tmpdir = Path(str(tmpdir))
    old_manager = deepcopy(configs.manager)
    try:
        paths = configs.ConfigPaths()
        paths.user_paths = [tmpdir / 'config']
        paths.site_paths = []
        configs.manager.replace(configs.ConfigManager(paths))
        yield configs.manager
    finally:
        configs.manager.replace(old_manager)


@pytest.fixture(scope='function')
def task_manager(tmpdir, config_manager):
    tmpdir = str(tmpdir)
    task_dir = Path(tmpdir) / 'task'
    task_dir.mkdir()
    return TaskManager(task_dir=task_dir)


@pytest.fixture(scope='function')
def language_manager(tmpdir, task_manager):
    return LanguageManager(task_manager)
