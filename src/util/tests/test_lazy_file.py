from pathlib import Path
from compat import fspath
from unittest import mock
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
    fi = LazyFile(fspath(file_path))
    assert not fi.text
    fi.text = 'hello'
    fi.save()
    assert file_path.open('r').read() == 'hello'

    fi = LazyFile(fspath(file_path))
    assert fi.text == 'hello'
    fi.text = '42'
    fi.save()
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
            fi = LazyFile(Path('file.txt'))
            assert fi.text == 'hello\nworld'
            cur_file.contents = '42'
            fi.load()
            assert fi.text == '42'
            fi.text = '43'
            fi.text = '42'
            assert cur_file.modify_count == 0
            fi.save()
            assert cur_file.modify_count == 0
            fi.text = '1385'
            fi.save()
            assert cur_file.modify_count == 1
            assert cur_file.contents == '1385'
