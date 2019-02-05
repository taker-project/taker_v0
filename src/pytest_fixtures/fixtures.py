from pathlib import Path
from copy import deepcopy
import pytest
import configs
from taskbuilder.manager import TaskManager


@pytest.fixture(scope='function')
def config_manager(tmpdir):
    tmpdir = Path(str(tmpdir))
    print(configs.manager)
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
