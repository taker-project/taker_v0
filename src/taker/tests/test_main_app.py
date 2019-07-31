import subprocess
from subprocess import PIPE
import pytest
import os
from compat import fspath
from ...pytest_fixtures import *


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
    res = subprocess.run(['take', '-h'], stdout=PIPE, stderr=PIPE,
                         check=True, universal_newlines=True)
    assert res.stdout.find('usage:') >= 0


def test_no_command():
    res = subprocess.run(['take'], stdout=PIPE, stderr=PIPE,
                         universal_newlines=True)
    assert res.returncode != 0
    assert res.stderr.find('no command specified') >= 0


def test_no_task_dir(tmpdir, monkeypatch):
    monkeypatch.chdir(tmpdir)
    make_source()
    res = subprocess.run(['take', 'compile', 'file.cpp'],
                         stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.returncode != 0
    assert res.stderr.find('you must be in task directory') >= 0


def test_compile(task_manager, monkeypatch):
    monkeypatch.chdir(fspath(task_manager.repo.directory))
    make_source()
    make_badsource()
    res = subprocess.run(['take', 'compile', 'file.cpp'],
                         stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.returncode == 0
    assert res.stdout.find('ok') >= 0

    res = subprocess.run(['take', 'compile', 'bad.cpp'],
                         stdout=PIPE, stderr=PIPE, universal_newlines=True)
    assert res.returncode != 0
    assert res.stdout.find('compilation error') >= 0
