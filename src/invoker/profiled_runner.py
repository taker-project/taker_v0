import os
import shutil
from pathlib import Path
from runners import Runner, IsolatePolicy, Status
from .config import config

# now the isolation is bound to the task directory
# these rules can be too broad
# TODO: make checker/generator isolation stricter!
# TODO: add execution profile for solutions!


class AbstractRunProfile:
    @staticmethod
    def name():
        raise NotImplementedError()

    def update_runner(self, runner):
        raise NotImplementedError()

    def __init__(self, repository):
        self.repository = repository


class ConfigRunProfile(AbstractRunProfile):
    @staticmethod
    def name():
        raise NotImplementedError()

    def _config_section(self):
        return config()[self.name()]

    def update_runner(self, runner):
        runner.parameters.time_limit = self._config_section()['time-limit']
        runner.parameters.memory_limit = self._config_section()['memory-limit']
        runner.parameters.isolate_dir = self.repository.directory
        runner.parameters.isolate_policy = IsolatePolicy.NORMAL
        runner.parameters.working_dir = Path(os.path.dirname(
            runner.parameters.executable))


class CompilerRunProfile(ConfigRunProfile):
    @staticmethod
    def name():
        return 'compiler'

    def update_runner(self, runner):
        super().update_runner(runner)
        runner.capture_stdout = True
        runner.capture_stderr = True
        runner.parameters.isolate_policy = IsolatePolicy.COMPILE


class CheckerRunProfile(ConfigRunProfile):
    @staticmethod
    def name():
        return 'checker'

    def update_runner(self, runner):
        super().update_runner(runner)
        runner.capture_stdout = True
        runner.capture_stderr = True


class ValidatorRunProfile(ConfigRunProfile):
    @staticmethod
    def name():
        return 'validator'

    def update_runner(self, runner):
        super().update_runner(runner)
        runner.parameters.isolate_policy = IsolatePolicy.STRICT
        runner.capture_stdout = True
        runner.capture_stderr = True


class GeneratorRunProfile(ConfigRunProfile):
    @staticmethod
    def name():
        return 'generator'

    def update_runner(self, runner):
        super().update_runner(runner)
        runner.parameters.isolate_policy = IsolatePolicy.STRICT
        runner.capture_stderr = True


__PROFILES = {}


def register_profile(profile_class):
    if profile_class in __PROFILES:
        raise KeyError(profile_class)
    __PROFILES[profile_class.name()] = profile_class


def create_profile(name, repository, **kwargs):
    return __PROFILES[name](repository, **kwargs)


def list_profiles():
    return __PROFILES.keys()


register_profile(CompilerRunProfile)
register_profile(CheckerRunProfile)
register_profile(ValidatorRunProfile)
register_profile(GeneratorRunProfile)


class ProfiledRunner:
    @property
    def results(self):
        return self.__runner.results

    @property
    def stdout(self):
        return self.__runner.stdout

    @property
    def stderr(self):
        return self.__runner.stderr

    @property
    def stdin(self):
        return self.__runner.stdin

    @stdin.setter
    def stdin(self, value):
        self.__runner.stdin = value

    def all_output(self):
        return self.stdout + self.stderr

    def run(self, cmdline, working_dir=None):
        for arg in cmdline:
            assert isinstance(arg, str)
        executable = os.path.abspath(cmdline[0])
        if not os.path.exists(executable):
            raise FileNotFoundError(executable)
        self.__runner.parameters.executable = executable
        self.__runner.parameters.args = cmdline[1:]
        self.profile.update_runner(self.__runner)
        if working_dir is not None:
            self.__runner.parameters.working_dir = working_dir
        self.__runner.run()

    def format_results(self):
        signal = ''
        if self.results.signal != 0:
            if self.results.signal_name:
                signal = 'signal: {} ({})\n'.format(self.results.signal,
                                                    self.results.signal_name)
            else:
                signal = 'signal: {}\n'.format(self.results.signal)
        msg = ('stdout:\n{}\nstderr:\n{}\ntime: {} sec\nmemory: {} MiB\n'
               'exitcode: {}\n{}status: {}\n')
        msg = msg.format(self.stdout, self.stderr, self.results.time,
                         self.results.memory, self.results.exitcode,
                         signal, repr(self.results.status))
        return msg

    def get_cli_exitcode(self):
        '''Returns the exitcode that will be used in CLI subcommands'''
        if self.results.exitcode != 0:
            return self.results.exitcode
        if self.results.signal != 0:
            return 128 + self.results.signal
        if self.results.status != Status.OK:
            return 1
        return 0

    def __init__(self, profile=None, runner_path=None):
        self.profile = profile
        self.__runner = Runner(runner_path)
