from cli import app_exe
from taskbuilder import InputFile, OutputFile, File
from .profiled_runner import ProfiledRunner
from .compiler import Compiler


class SourceCode:
    def compile(self):
        self.compiler.compile()

    def run(self, profile, custom_args=[]):
        self.runner.profile = profile
        self.runner.run(self.language.run_args(self.exe_file, custom_args))

    def add_compile_rule(self):
        try:
            if self.src_file.resolve() == self.exe_file.resolve():
                return None
        except FileNotFoundError:
            # the files cannot be equal if one of them doesn't exist :)
            # if we don't catch FileNotFoundError, it will fail tests on Py3.5
            pass
        makefile = self.task_manager.makefile
        rule = makefile.add_file_rule(self.exe_file)
        args = ['compile', OutputFile(self.exe_file, prefix='--exe='),
                '--lang=' + self.language.name]
        for dir in self.library_dirs:
            args.append(File(dir, prefix='--lib='))
        args += ['--', InputFile(self.src_file)]
        rule.add_global_cmd(app_exe(), args)
        return rule

    def __init__(self, manager, src_file, exe_file=None, language=None,
                 library_dirs=None):
        self.manager = manager
        self.task_manager = manager.task_manager
        if language is None:
            language = self.manager.get_ext(src_file.suffix)[0]
        self.compiler = Compiler(
            manager.repo, language, src_file, exe_file, library_dirs)
        self.runner = ProfiledRunner()
        self.src_file = self.compiler.src_file.absolute()
        self.exe_file = self.compiler.exe_file.absolute()
        self.language = language
        self.library_dirs = self.compiler.library_dirs
