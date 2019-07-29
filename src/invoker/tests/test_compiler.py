from invoker.config import CONFIG_NAME
from runners import Runner, Status
from pytest_fixtures import task_manager, config_manager
from invoker.compiler import Compiler, CompileError
from invoker.manager import LanguageManager
from os import path
import pytest
import shutil
from pathlib import Path
from invoker.utils import default_exe_ext


def tests_location():
    return Path(path.abspath(path.join('src', 'invoker', 'tests')))


def test_detect_language(config_manager, task_manager):
    language_manager = LanguageManager(task_manager.repo)

    tests = tests_location()

    assert language_manager.detect_language(
        tests / 'detect_lang.cpp').name == 'cpp.g++11'
    assert language_manager.detect_language(
        tests / 'code.cpp').name == 'cpp.g++17'
    with pytest.raises(CompileError):
        language_manager.detect_language(tests / 'compile_error.cpp')


def test_compiler(config_manager, task_manager, tmpdir):
    tmpdir = Path(tmpdir)
    repo = task_manager.repo

    language_manager = LanguageManager(repo)
    lang_cpp = language_manager.get_lang('cpp.g++14')
    lang_py = language_manager.get_lang('py.py3')

    src_dir = tmpdir / 'src'
    src_dir.mkdir()

    for fname in ['code.cpp', 'compile_error.cpp', 'code.py']:
        shutil.copy(tests_location() / fname, src_dir / fname)

    src_cpp1 = src_dir / 'code.cpp'
    src_cpp2 = src_dir / 'compile_error.cpp'
    src_py1 = src_dir / 'code.py'

    exe_cpp1 = src_dir / ('1-code' + default_exe_ext())
    exe_py1 = src_dir / ('1-code' + default_exe_ext())

    with pytest.raises(CompileError):
        compiler = Compiler(repo, lang_cpp, src_cpp2)
        compiler.compile()
    with pytest.raises(CompileError):
        compiler = Compiler(repo, lang_cpp, src_py1)
        compiler.compile()

    runner = Runner()
    runner.capture_stdout = True
    runner.capture_stderr = True

    compiler = Compiler(repo, lang_cpp, src_cpp1)
    compiler.compile()
    runner.parameters.executable = compiler.exe_file
    runner.run()
    assert runner.results.status == Status.OK
    assert runner.stdout == 'hello world\n'

    compiler = Compiler(repo, lang_py, src_py1)
    compiler.compile()
    runner.parameters.executable = lang_py.run_args(compiler.exe_file)[0]
    runner.parameters.args = lang_py.run_args(compiler.exe_file)[1:]
    runner.run()
    assert runner.results.status == Status.OK
    assert runner.stdout == 'hello world\n'

    compiler = Compiler(repo, lang_cpp, src_cpp1, exe_cpp1)
    compiler.compile()
    runner.parameters.executable = exe_cpp1
    runner.run()
    assert runner.results.status == Status.OK
    assert runner.stdout == 'hello world\n'

    compiler = Compiler(repo, lang_py, src_py1, exe_py1)
    compiler.compile()
    runner.parameters.executable = lang_py.run_args(exe_py1)[0]
    runner.parameters.args = lang_py.run_args(exe_py1)[1:]
    runner.run()
    assert runner.results.status == Status.OK
    assert runner.stdout == 'hello world\n'
