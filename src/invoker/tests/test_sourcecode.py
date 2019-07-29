import shutil
from os import path
from pathlib import Path
import pytest
from compat import fspath
from invoker.manager import LanguageManager
from invoker.profiled_runner import AbstractRunProfile
from invoker.compiler import CompileError
from pytest_fixtures import task_manager, config_manager


class EmptyRunProfile(AbstractRunProfile):
    @staticmethod
    def name():
        return 'empty'

    def update_runner(self, runner):
        runner.pass_stdin = True
        runner.capture_stdout = True


def tests_location():
    return Path(path.abspath(path.join('src', 'invoker', 'tests')))


def test_source_code(tmpdir, config_manager, task_manager):
    language_manager = LanguageManager(task_manager.repo)
    repo = task_manager.repo

    tmpdir = Path(str(tmpdir))
    (tmpdir / 'src').mkdir()
    src_cpp1 = tmpdir / 'src' / 'aplusb.cpp'
    shutil.copy(fspath(tests_location() / 'aplusb.cpp'), fspath(src_cpp1))

    lang1 = language_manager.get_lang('cpp.g++14')
    lang2 = language_manager.get_lang('pas.fpc')
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
