'''
Commands impelementation for build system

Important notice about paths in this module:

All paths are stored relative to the task directory. Except for AbsoluteFile,
where paths are stored as absolute. If you want to pass a relative path to the
command, please keep in mind that they should be relative to the task
directory, NOT to the current directory.

Also, the paths use pathlib.Path class and are not stored in "raw" string
format.
'''
from os import path
from pathlib import Path
import shlex
import shutil
from copy import copy, deepcopy
from enum import Enum, unique
from compat import fspath
from taskbuilder import utils

# TODO : Enable using windows cmd as a shell
# FIXME : Escape line breaks properly (?)


@unique
class CommandFlag(Enum):
    IGNORE = '-'
    SILENT = '@'
    FORCE = '+'


def command_flags_to_str(flags):
    return ''.join(sorted((f.value for f in flags)))


class File:
    def __eq__(self, other):
        return ((type(self) == type(other)) and
                (self.filename == other.filename))

    def __neq__(self, other):
        return not self == other

    def __str__(self):
        return self.__fspath__()

    def __fspath__(self):
        return fspath(self.filename)

    def __hash__(self):
        return hash(type(self)) ^ hash(self.filename)

    def __init__(self, filename):
        self.filename = Path(filename)

    def absolute(self, repo):
        return repo.abspath(self.filename)

    def normalize(self, repo):
        self.filename = repo.relpath(self.filename)

    def relative_to(self, repo, work_dir):
        abs_filename = self.absolute(repo)
        work_dir = repo.abspath(work_dir)
        return utils.relpath(abs_filename, work_dir)


class AbsoluteFile(File):
    def normalize(self, repo):
        self.filename = repo.abspath(self.filename)

    def relative_to(self, repo, work_dir):
        return self.filename


class NullFile(AbsoluteFile):
    def __init__(self):
        super().__init__(path.devnull)


class InputFile(File):
    pass


class OutputFile(File):
    pass


class Executable(File):
    def command_name(self, repo, work_dir):
        result = fspath(self.relative_to(repo, work_dir))
        if path.basename(result) == result:
            result = path.join(path.curdir, result)
        return result


class GlobalCmd(Executable):
    def relative_to(self, repo, work_dir):
        return self.filename

    def command_name(self, repo, work_dir):
        return fspath(self.filename)

    def normalize(self, repo):
        new_filename = shutil.which(fspath(self.filename))
        if new_filename is None:
            raise FileNotFoundError('command {} not found'
                                    .format(new_filename))
        self.filename = Path(new_filename)


class ShellCmd(GlobalCmd):
    def normalize(self, repo):
        pass


class AbstractCommand:
    def get_input_files(self):
        raise NotImplementedError()

    def get_output_files(self):
        raise NotImplementedError()

    def get_all_files(self):
        raise NotImplementedError()

    def _shell_str_internal(self):
        raise NotImplementedError()

    def shell_str(self):
        if fspath(self.work_dir) == path.curdir:
            return '{}{}'.format(command_flags_to_str(self.flags),
                                 self._shell_str_internal())
        return '{}cd {} && {}'.format(command_flags_to_str(self.flags),
                                      shlex.quote(fspath(self.work_dir)),
                                      self._shell_str_internal())

    def __init__(self, repo, work_dir=None, flags=None):
        if flags is None:
            flags = set()
        if work_dir is None:
            work_dir = repo.directory
        self.repo = repo
        self.work_dir = repo.relpath(work_dir)
        self.flags = flags


class Command(AbstractCommand):
    def __normalize_file(self, the_file):
        if not isinstance(the_file, File):
            return
        the_file.normalize(self.repo)

    def __executable_to_shell(self, exe):
        if isinstance(exe, Executable):
            return exe.command_name(self.repo, self.work_dir)
        raise TypeError('exe has invalid type (Executable expected)')

    def __arg_to_shell(self, arg):
        if isinstance(arg, str):
            return arg
        if isinstance(arg, File):
            return fspath(arg.relative_to(self.repo, self.work_dir))
        raise TypeError('arg has invalid type (str or File expected)')

    def __normalize_files(self):
        self.__normalize_file(self.executable)
        self.__normalize_file(self.stdin_redir)
        self.__normalize_file(self.stdout_redir)
        self.__normalize_file(self.stderr_redir)
        for the_file in self.args:
            self.__normalize_file(the_file)

    def __init__(self, repo, executable, args=[], work_dir=None, flags=None,
                 stdin_redir=None, stdout_redir=None, stderr_redir=None):
        super().__init__(repo, work_dir, flags)
        self.executable = copy(executable)
        self.args = deepcopy(args)
        self.stdin_redir = copy(stdin_redir)
        self.stdout_redir = copy(stdout_redir)
        self.stderr_redir = copy(stderr_redir)
        self.__normalize_files()

    def get_input_files(self):
        return [item
                for item in self.get_all_files()
                if isinstance(item, InputFile)]

    def get_output_files(self):
        return [item
                for item in self.get_all_files()
                if isinstance(item, OutputFile)]

    def get_all_files(self):
        possible_files = self.args + [self.stdin_redir, self.stdout_redir,
                                      self.stderr_redir, self.executable]
        return [item
                for item in possible_files
                if isinstance(item, File)]

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


class TouchCommand(Command):
    def __init__(self, repo, target_file):
        super().__init__(repo, GlobalCmd('touch'), args=[target_file])


class MakeDirCommand(Command):
    def __init__(self, repo, dirname, parents=False):
        args = []
        if parents:
            args += ['-p']
        args += [File(dirname)]
        super().__init__(repo, GlobalCmd('mkdir'), args=args)


class EchoCommand(Command):
    def __init__(self, repo, message, stdout_redir=None):
        super().__init__(repo, ShellCmd('echo'),
                         flags={CommandFlag.SILENT}, args=[message],
                         stdout_redir=stdout_redir)
