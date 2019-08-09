from pathlib import Path
from unittest import mock
from compat import fspath
from util import LazyFile


class FakeFile:
    def read(self):
        return self.contents

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def write(self, text):
        self.modify_count += 1
        self.contents = text

    def __init__(self, name, contents=''):
        self.name = name
        self.contents = contents
        self.modify_count = 0


def test_lazy_file(monkeypatch, tmpdir):
    tmpdir = Path(str(tmpdir))

    file_path = tmpdir / 'file.txt'
    file = LazyFile(fspath(file_path))
    assert not file.text
    file.text = 'hello'
    file.save()
    assert file_path.open('r').read() == 'hello'

    file = LazyFile(fspath(file_path))
    assert file.text == 'hello'
    file.text = '42'
    file.save()
    assert file_path.open('r').read() == '42'

    cur_file = FakeFile('file.txt', 'hello\nworld')

    def fake_exists(name):
        return True

    def fake_open(name, *args, **kwargs):
        nonlocal cur_file
        assert Path(cur_file.name) == name
        return cur_file

    with mock.patch.object(Path, 'open', fake_open):
        with mock.patch.object(Path, 'exists', fake_exists):
            file = LazyFile(Path('file.txt'))
            assert file.text == 'hello\nworld'
            cur_file.contents = '42'
            file.load()
            assert file.text == '42'
            file.text = '43'
            file.text = '42'
            assert cur_file.modify_count == 0
            file.save()
            assert cur_file.modify_count == 0
            file.text = '1385'
            file.save()
            assert cur_file.modify_count == 1
            assert cur_file.contents == '1385'
