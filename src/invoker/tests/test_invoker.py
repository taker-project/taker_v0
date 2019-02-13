import shutil
from pathlib import Path
from compat import fspath
from pytest_fixtures import *
from invoker.languages import *
from invoker.config import CONFIG_NAME


def test_languages(tmpdir, config_manager):
    tmpdir = Path(str(tmpdir))

    open(config_manager.user_config(CONFIG_NAME), 'w',
         encoding='utf8').write('''
[lang/sh.sh]
run-args = ['sh', '{exe}']
priority = 42
[lang/cpp.g++]
# Overwrite default g++
compile-args = ['g++', '{src}', '-o', '{exe}', '-Ofast']
priority = 1150
''')

    lang_manager = LanguageManagerBase()

    assert ([str(lang.name) for lang in lang_manager.get_ext('cpp')] ==
            ['cpp.g++14', 'cpp.g++', 'cpp.g++11'])
    assert lang_manager.get_ext('bad_ext') == []
    assert lang_manager['py.py2'].name == 'py.py2'
    assert lang_manager['py.py3'].name == 'py.py3'

    with pytest.raises(KeyError):
        lang_manager['bad_ext.bad_lang']

    lang = lang_manager['c.gcc']
    compile_arg_exp = [shutil.which('gcc'), fspath(Path.cwd() / 'file.cpp'),
                       '-o', fspath(Path.cwd() / 'file.exe'), '-O2',
                       '-I' + fspath(Path.cwd() / 'libs'),
                       '-I' + fspath(Path.cwd() / 'morelibs')]
    compile_arg_found = lang.compile_args(Path('file.cpp'), Path('file.exe'),
                                          [Path('libs'), Path('morelibs')])
    assert compile_arg_exp == compile_arg_found
    run_arg_exp = [fspath(tmpdir / 'file.exe'), 'arg1', 'arg2']
    with pytest.raises(FileNotFoundError):
        lang.run_args(tmpdir / 'file.exe')
    (tmpdir / 'file.exe').touch()
    (tmpdir / 'file.exe').chmod(0o755)
    assert run_arg_exp == lang.run_args(tmpdir / 'file.exe', ['arg1', 'arg2'])

    lang = lang_manager['cpp.g++']
    compile_arg_exp = [shutil.which('g++'), fspath(Path.cwd() / 'file.cpp'),
                       '-o', fspath(Path.cwd() / 'file.exe'), '-Ofast']
    compile_arg_found = lang.compile_args(Path('file.cpp'), Path('file.exe'))
    assert compile_arg_exp == compile_arg_found

    lang = lang_manager['sh.sh']
    assert lang.compile_args(Path('file.sh'), Path('file.exe')) is None
    run_arg_exp = [shutil.which('sh'), fspath(Path.cwd() / 'file.sh')]
    assert lang.run_args(Path('file.sh')) == run_arg_exp
