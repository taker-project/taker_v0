from os import path
import shutil
from pathlib import Path
import pytest
from compat import fspath
from runners import Runner, Status
from invoker.compiler import Compiler, CompileError
from invoker.utils import default_exe_ext
from .test_common import tests_location
from ...pytest_fixtures import *


def test_detect_language(language_manager):
    tests = tests_location()

    assert language_manager.detect_language(
        tests / 'detect_lang.cpp').name == 'cpp.g++11'
    assert language_manager.detect_language(
        tests / 'code.cpp').name == 'cpp.g++17'
    assert language_manager.detect_language(
        tests / 'code.py').name == 'py.py3'
    with pytest.raises(CompileError):
        language_manager.detect_language(tests / 'compile_error.cpp')
    with pytest.raises(CompileError):
        language_manager.detect_language(tests / 'code_unknown.red')


def test_compiler(tmpdir, task_manager, language_manager):
    tmpdir = Path(str(tmpdir))
    repo = task_manager.repo

    lang_cpp = language_manager.get_lang('cpp.g++14')
    lang_py = language_manager.get_lang('py.py3')

    src_dir = tmpdir / 'src'
    src_dir.mkdir()

    for fname in ['code.cpp', 'compile_error.cpp', 'code_libs.cpp', 'code.py']:
        shutil.copy(fspath(tests_location() / fname), fspath(src_dir / fname))

    src_cpp1 = src_dir / 'code.cpp'
    src_cpp2 = src_dir / 'compile_error.cpp'
    src_cpp3 = src_dir / 'code_libs.cpp'
    src_py1 = src_dir / 'code.py'
    src_bad1 = src_dir / 'bad_code.py'
    src_bad2 = src_dir / 'bad_code2.py'

    exe_cpp1 = src_dir / ('1-code' + default_exe_ext())
    exe_py1 = src_dir / ('1-code' + default_exe_ext())

    with pytest.raises(CompileError):
        compiler = Compiler(repo, lang_cpp, src_cpp2)
        compiler.compile()
    with pytest.raises(CompileError):
        compiler = Compiler(repo, lang_cpp, src_py1)
        compiler.compile()
    with pytest.raises(CompileError):
        compiler = Compiler(repo, lang_py, src_bad1, src_bad2)
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

    compiler = Compiler(repo, lang_cpp, src_cpp3,
                        library_dirs=[tests_location()])
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
