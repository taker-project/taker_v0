import os
import shutil
import pytest
from compat import fspath
from pathlib import Path
from invoker import CompileError, LanguageError
from invoker import default_exe_ext
from srclists.srclist import *
from ...pytest_fixtures import *


def tests_location():
    return (Path('src') / 'srclists' / 'tests' / 'src').absolute()


DEFAULT_CONFIG = '''\
[a_first.c]
lang: string = 'c.gcc'
exe-name: string = 'a_first'
[detect_c.c]
lang: string = 'c.gcc'
exe-name: string = 'detect_c'
[detect_cpp11.cpp]
lang: string = 'cpp.g++11'
exe-name: string = 'detect_cpp11'
[detect_py.py]
lang: string = 'py.py3'
exe-name: string = 'detect_py.py'
[samename.c]
lang: string = 'c.gcc'
exe-name: string = 'samename'
[samename.cpp]
lang: string = 'cpp.g++17'
exe-name: string = 'samename_1'
[samename.py]
lang: string = 'py.py3'
exe-name: string = 'samename.py'\
'''


@pytest.fixture(scope='function')
def srclist(config_manager, repo_manager, language_manager):
    path = repo_manager.task_dir
    src_dir = path / 'src'
    test_dir = tests_location()
    shutil.copytree(fspath(test_dir), fspath(src_dir))
    return SourceList('src', repo_manager, language_manager)


def test_sourcelist_basic(srclist, repo_manager, language_manager):
    src_dir = srclist.path

    assert srclist.list_add_candidates() == [
        'a_first.c', 'bad!name.cpp', 'compile_error.c', 'detect_c.c',
        'detect_cpp11.cpp', 'detect_py.py', 'samename.c', 'samename.cpp',
        'samename.py']

    with pytest.raises(SourceItemError):
        srclist.rescan_add()
    with pytest.raises(SourceItemError):
        srclist.rescan_add()
    assert not srclist
    exclist = srclist.rescan_add(True)
    assert len(exclist) == 2
    assert isinstance(exclist[0], SourceItemError)
    assert isinstance(exclist[1], CompileError)
    assert len(srclist) == 7
    srclist.save()

    config_file = DEFAULT_CONFIG
    assert (src_dir / 'list.take').open('r').read() == config_file

    del srclist
    config_file = config_file.replace("samename'", "42'")
    config_file += '\n[.sys]\nlang: string = "something wrong"'
    (src_dir / 'list.take').open('w').write(config_file)
    srclist = SourceList('src', repo_manager, language_manager)
    assert len(srclist) == 7
    assert srclist['samename.c'].exe_name == '42'

    (src_dir / 'detect_cpp11.cpp').unlink()
    with pytest.raises(SourceItemError):
        srclist.rescan_add()
    assert len(srclist) == 7
    srclist.rescan_remove()
    assert len(srclist) == 6
    assert 'detect_cpp11.cpp' not in srclist

    shutil.copy(fspath(src_dir / 'samename.cpp'), fspath(src_dir / 'file.cpp'))
    assert srclist.list_add_candidates() == [
        'bad!name.cpp', 'compile_error.c', 'file.cpp']

    srclist.rescan_add(True)
    assert 'file.cpp' in srclist
    assert len(srclist) == 7
    with pytest.raises(KeyError):
        srclist.remove('unknown.cpp')
    srclist.remove('file.cpp')
    assert len(srclist) == 6

    srclist['samename.c'].exe_name = '.badexe'
    with pytest.raises(SourceItemError):
        srclist.validate()
    srclist['samename.c'].exe_name = '42'


def test_sourcelist_validate(repo_manager, language_manager, srclist):
    src_dir = srclist.path

    new_cfg = DEFAULT_CONFIG.replace("samename'", "my/invalid_exe_name'")
    (src_dir / 'list.take').open('w').write(new_cfg)
    with pytest.raises(SourceItemError):
        new_srclist = SourceList('src', repo_manager, language_manager)
    new_cfg = DEFAULT_CONFIG.replace("cpp.g++11'", "bad-lang'")
    (src_dir / 'list.take').open('w').write(new_cfg)
    with pytest.raises(LanguageError):
        new_srclist = SourceList('src', repo_manager, language_manager)


def test_sourcelist_add_errors(repo_manager, language_manager, srclist):
    src_dir = srclist.path

    srclist._sys_files.add('detect_cpp11.cpp')
    with pytest.raises(SourceItemError):
        srclist.add('detect_cpp11.cpp')
    with pytest.raises(SourceItemError):
        srclist.add('bad!name.cpp')
    srclist.add('samename.c')
    with pytest.raises(SourceItemError):
        srclist.add('samename')
    with pytest.raises(SourceItemError):
        srclist.add('samename.c')


@pytest.fixture(scope='function')
def overwrite_config_samefile(config_manager):
    config = '''
[lang/newpy.newpy]
active = true
'''
    config_manager.user_config('invoker').open(
        'w', encoding='utf8').write(config)


def test_samefile(overwrite_config_samefile, language_manager, srclist):
    src_dir = srclist.path

    shutil.copy(fspath(src_dir / 'samename.py'),
                fspath(src_dir / 'samename.newpy'))

    language_manager.get_best_lang('.newpy')

    item1 = srclist.add('samename.c', 'c.gcc')
    item2 = srclist.add('samename.cpp', 'cpp.g++')
    item3 = srclist.add('samename.newpy', 'newpy.newpy')
    assert item1.exe_name == 'samename' + default_exe_ext()
    assert item2.exe_name == 'samename_1' + default_exe_ext()
    assert item3.exe_name == 'samename_2' + default_exe_ext()
    srclist.save()


def test_is_filename_valid():
    assert is_filename_valid('hello.cpp')
    assert is_filename_valid('hello')
    assert is_filename_valid('HeLLo')
    assert is_filename_valid('He123LLo')
    assert is_filename_valid('123')
    assert is_filename_valid('+-._')
    assert is_filename_valid('_._')
    assert not is_filename_valid('-file.txt')
    assert not is_filename_valid('')
    assert not is_filename_valid('file.tar.gz')
    assert not is_filename_valid('.file')
    assert not is_filename_valid('$.cpp')
    assert not is_filename_valid('my/file.txt')
    assert not is_filename_valid('/file')
    assert not is_filename_valid('Makefile.cpp')
    assert not is_filename_valid('Makefile')
