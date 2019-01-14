from taskbuilder.repository import *
from pathlib import Path
import pytest
from unittest import mock


def test_repo(tmpdir, monkeypatch):
    tmpdir = Path(str(tmpdir))
    task_dir = tmpdir / 'task'
    Path.mkdir(task_dir)

    repo = TaskRepository(Path(task_dir))
    repo.init_task()

    assert repo.relpath(Path(path.pardir) / path.curdir) == Path(path.pardir)
    assert repo.relpath(tmpdir) == Path(path.pardir)
    assert repo.abspath(Path(path.pardir) / path.curdir) == tmpdir
    assert repo.abspath(tmpdir) == tmpdir

    del repo

    with pytest.raises(FileNotFoundError):
        find_task_dir()

    new_dir = task_dir / 'parent' / 'subparent'
    Path.mkdir(new_dir, parents=True)
    Path.mkdir(tmpdir / '42')
    monkeypatch.chdir(str(new_dir))

    assert find_task_dir(task_dir) == task_dir
    assert find_task_dir(new_dir) == task_dir

    repo = TaskRepository(find_task_dir())
    assert repo.directory.samefile(task_dir)
    assert (repo.relpath(task_dir.parent / '42') ==
            Path(path.pardir) / '42')
    assert (repo.abspath(Path(path.pardir) / '42') ==
            task_dir.parent / '42')

    with mock.patch('os.chdir'):
        repo.to_task_dir()
        os.chdir.assert_called_once_with(str(task_dir))
