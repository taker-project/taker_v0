from os import path
import shutil
from .config import config
from compat import fspath


class Language:
    def _lang_section_name(self):
        return 'lang/' + self.name

    def _lang_section(self):
        return config()[self._lang_section_name()]

    def _compile_args_template(self):
        return self._lang_section()['compile-args']

    def _run_args_template(self):
        return self._lang_section()['run-args']

    def get_extensions(self):
        return self.name.split('.')[0]

    def _finalize_arglist(self, args):
        # get full path of the executable
        if not path.isabs(args[0]):
            first_arg = shutil.which(args[0])
            if first_arg is None:
                raise FileNotFoundError('cannot find executable "{}"'
                                        .format(args[0]))
            args[0] = first_arg

    def compile_args(self, src_file, exe_file, library_dirs):
        src_file = src_file.absolute()
        exe_file = exe_file.absolute()
        args_template = self._compile_args_template()
        assert(len(args_template) >= 1)
        res = []
        # FIXME : support {curly braces} inside the templates
        mapping = {
            'src': fspath(src_file),
            'exe': fspath(exe_file),
        }
        for arg in args_template:
            if arg.find('{lib}') >= 0:
                for lib in library_dirs:
                    mapping['lib'] = lib
                    res += [arg.format_map(mapping)]
                continue
            res += arg.format_map(mapping)
        self._finalize_arglist(res)
        return res

    def run_args(self, exe_file, custom_args):
        args_template = self._run_args_template()
        if not args_template:
            args_template = ['{exe}']
        mapping = {'exe': fspath(exe_file.resolve())}
        res = [args_template.format_map(mapping) for arg in args_template]

        # get full path of the executable
        first_arg = shutil.which(res[0])
        if first_arg is not None:
            res[0] = first_arg
        self._finalize_arglist(res)
        return res + custom_args

    def __lt__(self, other):
        return self.priority > other.priority

    def __init__(self, name, priority):
        self.name = name
        self.priority = priority


class PredefinedLanguage(Language):
    def _compile_args_template(self):
        return self.__compile_args_template

    def _run_args_template(self):
        return self.__run_args_template

    def __init__(self, name, priority, compile_args, run_args):
        super().__init__(self, name, priority)
        self.__compile_args_template = compile_args
        self.__run_args_template = run_args


class ConfigLanguage(Language):
    def _compile_args_template(self):
        return self.__compile_args_template

    def _run_args_template(self):
        return self.__run_args_template

    def __init__(self, section):
        assert section.key.startswith('lang/')
        prior = section.get_value('priority', 0)
        super().__init__(self, section.key.partition('/')[2])
        self.__compile_args_template = section.get_value('compile-args')
        self.__run_args_template = section.get_value('run-args')


class LanguageManagerBase:
    def add_language(self, language):
        name = language.name
        assert name not in self._languages
        self._languages[name] = language
        self._extensions.setdefault(name, [])
        self._extensions[name] += [language]

    def _predefine(self):
        self.add_language(PredefinedLanguage(
            'c.gcc',
            compile_args=['gcc', '{src}', '-o', '{exe}', '-O2', '-I{lib}']))
        self.add_language(PredefinedLanguage(
            'cpp.g++',
            compile_args=['g++', '{src}', '-o', '{exe}', '-O2', '-I{lib}']))
        self.add_language(PredefinedLanguage(
            'cpp.g++11',
            compile_args=['g++', '{src}', '-o', '{exe}', '-O2', '--std=c++11',
                          '-I{lib}']))
        self.add_language(PredefinedLanguage(
            'cpp.g++14',
            compile_args=['g++', '{src}', '-o', '{exe}', '-O2', '--std=c++14',
                          '-I{lib}']))
        self.add_language(PredefinedLanguage(
            'pas.fpc',
            compile_args=['fpc', '{src}', '-o{exe}', '-Fi{lib}', '-FU{lib}']
        ))
        self.add_language(PredefinedLanguage(
            'py.py2',
            compile_args=['cp', '{src}', '{exe}'],
            run_args=['python2', '{exe}']
        ))
        self.add_language(PredefinedLanguage(
            'py.py3',
            compile_args=['cp', '{src}', '{exe}'],
            run_args=['python3', '{exe}']
        ))
        # TODO : add more languages!

    def reload(self):
        self._languages.clear()
        self._extensions.clear()
        self._predefine()
        for section in config():
            if section.key.startswith('lang/'):
                self.add_language(ConfigLanguage(section))

    def __init__(self):
        self._languages = {}
        self._extensions = {}
        self.reload()
