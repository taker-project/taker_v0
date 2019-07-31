from .profiled_runner import ProfiledRunner
from .compiler import Compiler


class SourceCode:
    def compile(self):
        self.compiler.compile()

    def run(self, profile, custom_args=[]):
        self.runner.profile = profile
        self.runner.run(self.language.run_args(self.exe_file, custom_args))

    def __init__(self, manager, src_file, exe_file=None, language=None,
                 library_dirs=None):
        self.manager = manager
        self.task_manager = manager.task_manager
        if language is None:
            language = self.manager.get_ext(src_file.suffix)[0]
        self.compiler = Compiler(
            manager.repo, language, src_file, exe_file, library_dirs)
        self.runner = ProfiledRunner()
        self.src_file = self.compiler.src_file
        self.exe_file = self.compiler.exe_file
        self.language = language
        self.library_dirs = self.compiler.library_dirs
