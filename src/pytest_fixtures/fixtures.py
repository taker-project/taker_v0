from pathlib import Path
from copy import deepcopy
from unittest import mock
import shutil
import pytest
import configs
from taskbuilder.manager import TaskManager
from invoker import LanguageManager
import cli


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


@pytest.fixture(scope='function')
def taker_app():
    def mock_app_exe(name=None):
        return Path(shutil.which('take'))

    with mock.patch('cli.app_exe', new_callable=mock_app_exe):
        yield mock_app_exe()
