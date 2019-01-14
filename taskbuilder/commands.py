from os import path
from pathlib import Path
import shlex
import shutil
import warnings
from copy import copy, deepcopy
from . import utils

# TODO : Enable using windows cmd as a shell
# TODO : Escape line breaks properly (?)

'''
Important notice about paths in this module:

All paths are stored relative to the task directory. Except for AbsoluteFile,
where paths are stored as absolute. If you want to pass a relative path to the
command, please keep in mind that they should be relative to the task
directory, NOT to the current directory.

Also, the paths use pathlib.Path class and are not stored in "raw" string
format.
'''


class File:
    def __eq__(self, other):
        return ((type(self) == type(other)) and
                (self.filename == other.filename))

    def __neq__(self, other):
        return not (self == other)

    def __str__(self):
        return str(self.filename)

    def __init__(self, filename):
        self.filename = Path(filename)

    def absolute(self, manager):
        return manager.abspath(self.filename)

    def normalize(self, manager):
        if self.filename.is_absolute():
            self.filename = manager.relpath(self.filename)

    def relative_to(self, manager, work_dir):
        abs_filename = manager.abspath(self.filename)
        return utils.relpath(abs_filename, work_dir)


class AbsoluteFile(File):
    def normalize(self, manager):
        self.filename = utils.abspath(self.filename)

    def relative_to(self, manager, work_dir):
        return self.filename


class NullFile(AbsoluteFile):
    def __init__(self):
        self.filename = Path(path.devnull)


class InputFile(File):
    pass


class OutputFile(File):
    pass


class Executable(File):
    def command_name(self, manager, work_dir):
        result = str(self.relative_to(manager, work_dir))
        if path.basename(result) == result:
            result = path.join(path.curdir, result)
        return result


class GlobalCmd(Executable):
    def relative_to(self, manager, work_dir):
        return self.filename

    def command_name(self, manager, work_dir):
        return str(self.filename)

    def normalize(self, manager):
        new_filename = Path(shutil.which(str(self.filename)))
        if new_filename is None:
            # FIXME : maybe raise an error here?
            warnings.warn('command {} not found'.format(new_filename))
            return
        self.filename = new_filename


class AbstractCommand:
    def get_input_files():
        raise NotImplementedError()

    def get_output_files():
        raise NotImplementedError()

    def _shell_str_internal():
        raise NotImplementedError()

    def shell_str(self):
        if str(self.work_dir) == path.curdir:
            return self._shell_str_internal()
        return 'cd {} && {}'.format(shlex.quote(str(self.work_dir)),
                                    self._shell_str_internal())

    def work_dir_abs(self):
        return self.manager.abspath(self.work_dir)

    def __init__(self, manager, work_dir=None):
        if work_dir is None:
            work_dir = manager.directory
        self.manager = manager
        self.work_dir = manager.relpath(work_dir)


class Command(AbstractCommand):
    def __normalize_file(self, the_file):
        if not isinstance(the_file, File):
            return
        the_file.normalize(self.manager)

    def __executable_to_shell(self, exe):
        if isinstance(exe, Executable):
            return exe.command_name(self.manager, self.work_dir_abs())
        raise TypeError('exe has invalid type (Executable expected)')

    def __arg_to_shell(self, arg):
        if isinstance(arg, str):
            return arg
        if isinstance(arg, File):
            return str(arg.relative_to(self.manager, self.work_dir_abs()))
        raise TypeError('arg has invalid type (str or File expected)')

    def __normalize_files(self):
        self.__normalize_file(self.executable)
        self.__normalize_file(self.stdin_redir)
        self.__normalize_file(self.stdout_redir)
        self.__normalize_file(self.stderr_redir)
        for the_file in self.args:
            self.__normalize_file(the_file)

    def __init__(self, manager, executable, work_dir=None, args=[],
                 stdin_redir=None, stdout_redir=None, stderr_redir=None):
        super().__init__(manager, work_dir)
        self.executable = executable
        self.args = deepcopy(args)
        self.stdin_redir = stdin_redir
        self.stdout_redir = stdout_redir
        self.stderr_redir = stderr_redir
        self.__normalize_files()

    def get_input_files(self):
        return [item for item in self.args + [self.stdin_redir]
                if isinstance(item, InputFile)]

    def get_output_files(self):
        return [item
                for item in self.args + [self.stdout_redir, self.stderr_redir]
                if isinstance(item, OutputFile)]

    def _shell_str_internal(self):
        result = shlex.quote(self.__executable_to_shell(self.executable))
        for arg in self.args:
            result += ' ' + shlex.quote(self.__arg_to_shell(arg))
        if self.stdin_redir is not None:
            result += ' <'
            result += shlex.quote(self.__arg_to_shell(self.stdin_redir))
        if self.stdout_redir is not None:
            result += ' >'
            result += shlex.quote(self.__arg_to_shell(self.stdout_redir))
        if self.stderr_redir is not None:
            result += ' 2>'
            result += shlex.quote(self.__arg_to_shell(self.stderr_redir))
        return result
