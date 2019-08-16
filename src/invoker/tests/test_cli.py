import subprocess
from subprocess import PIPE
import os
import shutil
from os import path
from pathlib import Path
import pytest
from compat import fspath
from invoker import default_exe_ext
from invoker.cli_base import INVOKER_CMD_NAME
from ...pytest_fixtures import *


def tests_location():
    return Path(path.abspath(path.join('src', 'invoker', 'tests')))


def bad_exe_location():
    return Path(path.abspath(path.join('src', 'runners', 'tests', 'build',
                                       'broken_test' + default_exe_ext())))


def make_source():
    open('file.cpp', 'w').write('''\
#include <stdio.h>

int main() {
    int a, b; scanf("%d%d", &a, &b);
    printf("%d\\n", a + b);
    return 0;
}
''')


def make_badsource():
    open('bad.cpp', 'w').write('Compile error!')


def test_help():
    res = subprocess.run([INVOKER_CMD_NAME, '-h'], stdout=PIPE, stderr=PIPE,
                         check=True, universal_newlines=True)
    assert res.stdout.find('usage:') >= 0


def test_no_command():
    res = subprocess.run([INVOKER_CMD_NAME], stdout=PIPE, stderr=PIPE,
                         universal_newlines=True)
    assert res.returncode != 0
    assert res.stderr.find('no command specified') >= 0


def test_no_task_dir(tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)
    make_source()
    res = subprocess.run([INVOKER_CMD_NAME, 'compile', 'file.cpp'],
                         stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.returncode != 0
    assert res.stderr.find('you must be in task directory') >= 0


def test_compile(repo_manager, monkeypatch):
    monkeypatch.chdir(fspath(repo_manager.repo.directory))
    make_source()
    make_badsource()
    res = subprocess.run([INVOKER_CMD_NAME, 'compile', 'file.cpp'],
                         stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.returncode == 0
    assert res.stdout.find('ok') >= 0

    res = subprocess.run([INVOKER_CMD_NAME, 'compile', 'bad.cpp'],
                         stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.returncode != 0
    assert res.stdout.find('compilation error') >= 0


def test_run(repo_manager, monkeypatch):
    tests_loc = tests_location()
    badexe_loc = bad_exe_location()

    monkeypatch.chdir(fspath(repo_manager.repo.directory))

    shutil.copy(fspath(tests_loc / 'code_div.cpp'), '.')
    subprocess.run([INVOKER_CMD_NAME, 'compile', 'code_div.cpp'], check=True,
                   stdout=PIPE, stderr=PIPE, universal_newlines=True)

    code_div_exe = 'code_div' + default_exe_ext()

    open('input.txt', 'w').write('12 3')
    res = subprocess.run(
        [INVOKER_CMD_NAME, 'run', code_div_exe, '-p', 'compiler'],
        check=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.stdout.startswith('stdout:\n4\n\nstderr:\n')

    res = subprocess.run(
        [INVOKER_CMD_NAME, 'run', code_div_exe, '-p', 'compiler', '-q'],
        check=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.stdout == '4\n'
    assert res.stderr == 'done\n'

    open('input.txt', 'w').write('12 0')
    res = subprocess.run(
        [INVOKER_CMD_NAME, 'run', code_div_exe, '-p', 'compiler'],
        stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.returncode != 0
    assert res.stdout.find('runtime-error') >= 0
    assert res.stdout.find('signal: ') >= 0

    os.mkdir('work')
    inner_in = Path('work') / 'input.txt'
    inner_in.open('w').write('42 6')
    res = subprocess.run(
        [INVOKER_CMD_NAME, 'run', code_div_exe, '-p', 'compiler', '-q', '-w',
         'work'], check=True, stdout=PIPE, stderr=PIPE,
        universal_newlines=True)
    assert res.stdout == '7\n'

    res = subprocess.run(
        [INVOKER_CMD_NAME, 'run', fspath(badexe_loc), '-p', 'compiler'],
        stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.returncode != 0
    assert res.stdout.find('run-fail') >= 0

    res = subprocess.run(
        [INVOKER_CMD_NAME, 'run', fspath(badexe_loc), '-p', 'compiler', '-q'],
        stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.returncode != 0
    assert res.stdout == ''
    assert res.stderr.find('error: program exited with status run-fail') >= 0
