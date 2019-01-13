from taskbuilder import manager
from taskbuilder.manager import *
from pathlib import Path
import pytest
from unittest import mock


def test_manager(tmpdir, monkeypatch):
    tmpdir = Path(str(tmpdir))
    task_dir = tmpdir / 'task'
    Path.mkdir(task_dir)

    mgr = TaskManager(Path(task_dir))
    mgr.init_task()
    del mgr

    with pytest.raises(FileNotFoundError):
        find_task_dir()
    with pytest.raises(FileNotFoundError):
        manager()

    new_dir = task_dir / 'parent' / 'subparent'
    Path.mkdir(new_dir, parents=True)
    Path.mkdir(tmpdir / '42')
    monkeypatch.chdir(str(new_dir))

    assert find_task_dir(task_dir) == task_dir
    assert find_task_dir(new_dir) == task_dir

    assert manager().directory.samefile(task_dir)
    assert manager().relpath(task_dir.parent / '42') == Path('..') / '42'
    assert manager().abspath(Path('..') / '42') == task_dir.parent / '42'

    with mock.patch('os.chdir'):
        manager().to_root_dir()
        os.chdir.assert_called_once_with(str(task_dir))

    # clean global state
    manager.task_manager = None
