from .profiled_runner import ProfiledRunner, CompilerRunProfile
from .languages import Language
from taskbuilder import TaskRepository
import os
import shutil
from tempfile import mkdtemp
from pathlib import Path
from runners import Status


class CompileError(Exception):
    pass


class Compiler:
    def compile(self):
        if not self.language.compile_args(self.src_file, self.exe_file):
            # just copy the file
            if not self.save_exe:
                return
            if os.path.samefile(self.src_file, self.exe_file):
                return
            try:
                shutil.copy(self.src_file, self.dst_file)
            except OSError as e:
                raise CompileError(
                    'could not copy file due to OS error: {}'
                    .format(e.strerror))
            return
        temp_dir = Path(
            mkdtemp('compilebox', '', self.repo.internal_dir(True)))
        try:
            src = temp_dir / os.path.basename(self.src_file)
            exe = temp_dir / os.path.basename(self.exe_file)
            shutil.copy(self.src_file, src)
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
                shutil.copy(exe, self.exe_file)
        except OSError as e:
            raise CompileError(
                'could not copy file due to OS error: {}'.format(e.strerror))
        finally:
            shutil.rmtree(temp_dir)

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
        self.src_file = os.path.abspath(src_file)
        if exe_file is None:
            exe_file = os.path.splitext(src_file)[0] + language.exe_ext
        self.exe_file = os.path.abspath(exe_file)
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
        except CompileError as e:
            if err is None:
                err = e
    if err is not None:
        raise e
    return None
