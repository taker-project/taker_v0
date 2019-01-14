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

    assert mgr.relpath(Path(path.pardir) / path.curdir) == Path(path.pardir)
    assert mgr.relpath(tmpdir) == Path(path.pardir)
    assert mgr.abspath(Path(path.pardir) / path.curdir) == tmpdir
    assert mgr.abspath(tmpdir) == tmpdir

    del mgr

    with pytest.raises(FileNotFoundError):
        find_task_dir()

    new_dir = task_dir / 'parent' / 'subparent'
    Path.mkdir(new_dir, parents=True)
    Path.mkdir(tmpdir / '42')
    monkeypatch.chdir(str(new_dir))

    assert find_task_dir(task_dir) == task_dir
    assert find_task_dir(new_dir) == task_dir

    manager = TaskManager(find_task_dir())
    assert manager.directory.samefile(task_dir)
    assert (manager.relpath(task_dir.parent / '42') ==
            Path(path.pardir) / '42')
    assert (manager.abspath(Path(path.pardir) / '42') ==
            task_dir.parent / '42')

    with mock.patch('os.chdir'):
        manager.to_root_dir()
        os.chdir.assert_called_once_with(str(task_dir))
