import shutil
from os import path
from pathlib import Path
import pytest
from compat import fspath
from invoker.profiled_runner import AbstractRunProfile
from invoker.compiler import CompileError
from ...pytest_fixtures import *


class EmptyRunProfile(AbstractRunProfile):
    @staticmethod
    def name():
        return 'empty'

    def update_runner(self, runner):
        runner.pass_stdin = True
        runner.capture_stdout = True


def tests_location():
    return Path(path.abspath(path.join('src', 'invoker', 'tests')))


def test_source_code(tmpdir, language_manager, task_manager):
    repo = task_manager.repo

    tmpdir = Path(str(tmpdir))
    (tmpdir / 'src').mkdir()
    src_cpp1 = tmpdir / 'src' / 'aplusb.cpp'
    src_py1 = tmpdir / 'src' / 'code.py'
    shutil.copy(fspath(tests_location() / 'aplusb.cpp'), fspath(src_cpp1))
    shutil.copy(fspath(tests_location() / 'code.py'), fspath(src_py1))

    lang1 = language_manager.get_lang('cpp.g++11')
    lang2 = language_manager.get_lang('cpp.g++14')
    src1 = language_manager.create_source(src_cpp1, language=lang1)
    src1.compile()
    src1.runner.stdin = '2 3'
    assert src1.runner.stdin == '2 3'
    src1.run(EmptyRunProfile(repo))
    assert src1.runner.stdout == '5\n'
    assert src1.runner.stderr == ''

    src2 = language_manager.create_source(src_cpp1, language=lang2)
    with pytest.raises(CompileError):
        src2.compile()

    src3 = language_manager.create_source(src_py1)
    src3.compile()
    src3.run(EmptyRunProfile(repo))
    assert src3.runner.stdout == 'hello world\n'
