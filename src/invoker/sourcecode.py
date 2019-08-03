from cli import app_exe
from taskbuilder import InputFile, OutputFile, File
from .profiled_runner import ProfiledRunner
from .compiler import Compiler


class SourceCode:
    def compile(self):
        self.compiler.compile()

    def run(self, profile, custom_args=[], working_dir=None):
        self.runner.profile = profile
        self.runner.run(self.language.run_args(self.exe_file, custom_args),
                        working_dir)

    def add_compile_rule(self):
        try:
            if self.src_file.resolve() == self.exe_file.resolve():
                return None
        except FileNotFoundError:
            # the files cannot be equal if one of them doesn't exist :)
            # if we don't catch FileNotFoundError, it will fail tests on Py3.5
            pass
        makefile = self.repo_manager.makefile
        rule = makefile.add_file_rule(self.exe_file)
        args = ['compile', OutputFile(self.exe_file, prefix='--exe='),
                '--lang=' + self.language.name]
        for dir in self.library_dirs:
            args.append(File(dir, prefix='--lib='))
        args += ['--', InputFile(self.src_file)]
        rule.add_global_cmd(app_exe(), args)
        return rule

    def add_run_command(self, rule, profile, custom_args=None, stdin='',
                        quiet=False, working_dir=None):
        if not isinstance(profile, str):
            profile = profile.name()
        args = ['run', '--lang=' + self.language.name, '--profile=' + profile]
        if working_dir is not None:
            args.append(File(working_dir.absolute(), prefix='--work-dir='))
        if stdin:
            args.append('--input=' + stdin)
        if quiet:
            args.append('-q')
        if custom_args is None:
            custom_args = []
        args += ['--', InputFile(self.exe_file)] + custom_args
        rule.add_global_cmd(app_exe(), args)

    def __init__(self, manager, src_file, exe_file=None, language=None,
                 library_dirs=None):
        self.manager = manager
        self.repo_manager = manager.repo_manager
        if language is None:
            language = self.manager.get_best_lang(src_file.suffix)
        self.compiler = Compiler(
            manager.repo, language, src_file, exe_file, library_dirs)
        self.runner = ProfiledRunner()
        self.src_file = self.compiler.src_file.absolute()
        self.exe_file = self.compiler.exe_file.absolute()
        self.language = language
        self.library_dirs = self.compiler.library_dirs
