from pathlib import Path
from copy import deepcopy
from unittest import mock
import shutil
import pytest
import configs
from taskbuilder.manager import RepositoryManager
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
def repo_manager(tmpdir, config_manager):
    tmpdir = str(tmpdir)
    task_dir = Path(tmpdir) / 'task'
    task_dir.mkdir()
    return RepositoryManager(task_dir=task_dir)


@pytest.fixture(scope='function')
def language_manager(tmpdir, repo_manager):
    return LanguageManager(repo_manager)


@pytest.fixture(scope='function')
def taker_app(monkeypatch):
    def mock_app_exe(name=None):
        return Path(shutil.which('take'))

    monkeypatch.setattr(cli, 'app_exe', mock_app_exe)
    return cli.app_exe()
