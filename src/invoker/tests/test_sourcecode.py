import shutil
from pathlib import Path
import pytest
from compat import fspath
from invoker.profiled_runner import AbstractRunProfile, CompilerRunProfile
from invoker.compiler import CompileError
from invoker.cli_base import invoker_exe
from .test_common import tests_location
from ...pytest_fixtures import *


class EmptyRunProfile(AbstractRunProfile):
    @staticmethod
    def name():
        return 'empty'

    def update_runner(self, runner):
        runner.pass_stdin = True
        runner.capture_stdout = True


def test_source_code(tmpdir, language_manager, repo_manager):
    repo = repo_manager.repo

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


def test_make_rules(tmpdir, language_manager, repo_manager):
    repo = repo_manager.repo

    tmpdir = Path(str(tmpdir))
    (tmpdir / 'task' / 'src').mkdir()
    lib_dir = tmpdir / 'task' / 'lib'
    lib_dir.mkdir()

    src_cpp1 = tmpdir / 'task' / 'src' / 'aplusb.cpp'
    src_cpp2 = tmpdir / 'task' / 'src' / 'code_libs.cpp'
    src_cpp3 = tmpdir / 'task' / 'src' / 'code_gen_out.cpp'
    src_cpplib = tmpdir / 'task' / 'lib' / 'code_mylib.h'
    src_py1 = tmpdir / 'task' / 'src' / 'code.py'
    shutil.copy(fspath(tests_location() / 'aplusb.cpp'), fspath(src_cpp1))
    shutil.copy(fspath(tests_location() / 'code_libs.cpp'), fspath(src_cpp2))
    shutil.copy(fspath(tests_location() / 'code_gen_out.cpp'),
                fspath(src_cpp3))
    shutil.copy(fspath(tests_location() / 'code_mylib.h'), fspath(src_cpplib))
    shutil.copy(fspath(tests_location() / 'code.py'), fspath(src_py1))

    src1 = language_manager.create_source(src_cpp1, language='cpp.g++11')
    rule1 = src1.add_compile_rule()
    src2 = language_manager.create_source(src_cpp2, language='cpp.g++14',
                                          library_dirs=[lib_dir])
    rule2 = src2.add_compile_rule()
    src3 = language_manager.create_source(src_py1)
    rule3 = src3.add_compile_rule()
    src4 = language_manager.create_source(src_cpp3)
    rule4 = src4.add_compile_rule()

    rule5 = repo_manager.makefile.add_phony_rule('genout')
    src4.add_run_command(rule5, CompilerRunProfile(repo), ['arg1', 'arg2'])
    src4.add_run_command(rule5, 'generator', quiet=True, stdin="see '42'!",
                         working_dir=tmpdir)

    assert rule3 is None
    assert rule4 is not None
    repo_manager.makefile.all_rule.add_depend(rule1)
    repo_manager.makefile.all_rule.add_depend(rule2)
    repo_manager.makefile.all_rule.add_depend(rule3)
    repo_manager.makefile.all_rule.add_depend(rule5)

    make_template = (tests_location() / 'srcbuild.make').open('r').read()
    make_template = make_template.format(invoker_exe())

    assert repo_manager.makefile.dump() == make_template

    repo_manager.build()
    assert src1.exe_file.exists()
    assert src2.exe_file.exists()
    assert src3.exe_file.exists()
    assert (tmpdir / 'output.txt').exists()
    assert (tmpdir / 'task' / 'src' / 'output.txt').exists()
