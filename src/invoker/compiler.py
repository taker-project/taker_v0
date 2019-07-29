import os
import shutil
from tempfile import mkdtemp
from pathlib import Path
from runners import Status
from compat import fspath
from .profiled_runner import ProfiledRunner, CompilerRunProfile


class CompileError(Exception):
    pass


class Compiler:
    def compile(self):
        if not self.language.compile_args(self.src_file, self.exe_file):
            # just copy the file
            if not self.save_exe:
                return
            if os.path.samefile(fspath(self.src_file), fspath(self.exe_file)):
                return
            try:
                shutil.copy(fspath(self.src_file), fspath(self.exe_file))
            except OSError as exc:
                raise CompileError(
                    'could not copy file due to OS error: {}'
                    .format(exc.strerror))
            return
        temp_dir = Path(
            mkdtemp('compilebox', '', fspath(self.repo.internal_dir(True))))
        try:
            src = temp_dir / self.src_file.name
            exe = temp_dir / self.exe_file.name
            shutil.copy(fspath(self.src_file), fspath(src))
            self.__runner.run(
                self.language.compile_args(src, exe, self.library_dirs))
            self.compiler_output = ('stdout:\n{}\nstderr:\n{}\ntime: {}\n'
                                    'memory: {}\nstatus: {}\n')
            self.compiler_output = self.compiler_output.format(
                self.__runner.stdout, self.__runner.stderr,
                self.__runner.results.time, self.__runner.results.memory,
                self.__runner.results.status)
            if self.__runner.results.status != Status.OK:
                raise CompileError('Compilation failed\n' +
                                   self.compiler_output)
            if self.save_exe:
                shutil.copy(fspath(exe), fspath(self.exe_file))
        except OSError as exc:
            raise CompileError(
                'could not copy file due to OS error: {}'.format(exc.strerror))
        finally:
            shutil.rmtree(fspath(temp_dir))

    def __init__(self, repo, language, src_file, exe_file=None,
                 library_dirs=None, save_exe=True):
        """
        Creates the Compiler object instance

        Parameters:
        repo (TaskRepository): task repository in use
        language (Language): programming language in use
        src_file (str): source file to compile
        exe_file (str): target executable. If None, the file name is deduced
          automatically.
        library_dirs (list): library paths in use. If None, no library paths
          are used.
        save_exe (bool): if False, exe is not saved to exe_file and is removed
        """
        self.repo = repo
        self.language = language
        self.src_file = src_file.absolute()
        if exe_file is None:
            exe_file = src_file.with_suffix(language.exe_ext)
        self.exe_file = exe_file.absolute()
        if library_dirs is None:
            library_dirs = []
        self.library_dirs = library_dirs
        self.__runner = ProfiledRunner(CompilerRunProfile(repo))
        self.compiler_output = ''
        self.save_exe = save_exe


def detect_language(repo, lang_list, src_file, library_dirs=None):
    err = None
    for lang in sorted(lang_list):
        compiler = Compiler(repo, lang, src_file, library_dirs=library_dirs,
                            save_exe=False)
        try:
            compiler.compile()
            return lang
        except CompileError as exc:
            if err is None:
                err = exc
    if err is not None:
        raise err
    raise CompileError('unable to detect language: none available')
