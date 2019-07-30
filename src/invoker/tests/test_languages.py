import shutil
from pathlib import Path
from compat import fspath
from ...pytest_fixtures import *
from invoker.languages import *
from invoker.utils import *
from invoker.config import CONFIG_NAME


def test_languages(tmpdir, config_manager):
    tmpdir = Path(str(tmpdir))

    config = '''
[lang/sh.sh]
run-args = ['sh', '{exe}']
priority = 42
exe-ext = '.sh'
[lang/cpp.g++]
# Overwrite default g++
compile-args = ['<cpp-compiler>', '{src}', '-o', '{exe}', '-Ofast']
priority = 1150
exe-ext = '.42.exe'
[lang/cpp.g++14]
active = false
'''

    c_compiler = shutil.which('gcc')
    if not c_compiler:
        c_compiler = shutil.which('clang')
    cpp_compiler = shutil.which('g++')
    if not cpp_compiler:
        cpp_compiler = shutil.which('clang++')

    config = config.replace('<cpp-compiler>', cpp_compiler)

    config_manager.user_config(CONFIG_NAME).open(
        'w', encoding='utf8').write(config)

    lang_manager = LanguageManagerBase()

    assert ([str(lang.name) for lang in lang_manager.get_ext('.cpp')] ==
            ['cpp.g++17', 'cpp.g++', 'cpp.g++11'])
    assert lang_manager.get_ext('.bad_ext') == []
    assert lang_manager['py.py2'].name == 'py.py2'
    assert lang_manager['py.py3'].name == 'py.py3'
    assert lang_manager['py.py3'].exe_ext == '.py'

    with pytest.raises(KeyError):
        lang_manager['bad_ext.bad_lang']

    with pytest.raises(ValueError):
        Language('q.q', exe_ext='iNeedDot')

    lang = lang_manager['c.gcc']
    compile_arg_exp = [c_compiler, fspath(Path.cwd() / 'file.cpp'),
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
    assert lang.exe_ext == default_exe_ext()

    lang = lang_manager['cpp.g++']
    compile_arg_exp = [cpp_compiler, fspath(Path.cwd() / 'file.cpp'),
                       '-o', fspath(Path.cwd() / 'file.exe'), '-Ofast']
    compile_arg_found = lang.compile_args(Path('file.cpp'), Path('file.exe'))
    assert compile_arg_exp == compile_arg_found
    assert lang.exe_ext == '.42.exe'

    lang = lang_manager['sh.sh']
    assert lang.compile_args(Path('file.sh'), Path('file.exe')) is None
    run_arg_exp = [shutil.which('sh'), fspath(Path.cwd() / 'file.sh')]
    assert lang.run_args(Path('file.sh')) == run_arg_exp
    assert lang.exe_ext == '.sh'
