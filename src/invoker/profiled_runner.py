from runners import Runner, IsolatePolicy
from .config import config
import os
import shutil

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
        runner.parameters.working_dir = os.path.dirname(
            runner.parameters.executable)


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
        runner.capture_stderr = True


class ValidatorRunProfile(ConfigRunProfile):
    @staticmethod
    def name():
        return 'validator'

    def update_runner(self, runner):
        super().update_runner(runner)
        runner.parameters.isolate_policy = IsolatePolicy.STRICT
        runner.capture_stderr = True


class GeneratorRunProfile(ConfigRunProfile):
    @staticmethod
    def name():
        return 'generator'

    def update_runner(self, runner):
        super().update_runner(runner)
        runner.parameters.isolate_policy = IsolatePolicy.STRICT


__PROFILES = {}


def register_profile(profile_class):
    if profile_class in __PROFILES:
        raise KeyError(profile_class)
    __PROFILES[profile_class.name()] = profile_class


def create_profile(name, repository, **kwargs):
    return __PROFILES[name](repository, **kwargs)


register_profile(CompilerRunProfile)
register_profile(CheckerRunProfile)
register_profile(ValidatorRunProfile)
register_profile(GeneratorRunProfile)


class ProfiledRunner:
    @property
    def results(self):
        return self.runner.results

    @property
    def stdout(self):
        return self.runner.stdout

    @property
    def stderr(self):
        return self.runner.stderr

    @property
    def stdin(self):
        return self.runner.stdin

    @stdin.setter
    def stdin(self, value):
        self.runner.stdin = value

    @property
    def parameters(self):
        return self.runner.parameters

    @parameters.setter
    def parameters(self, value):
        self.runner.parameters = value

    def run(self, cmdline):
        executable = shutil.which(cmdline[0])
        if not os.path.exists(executable):
            raise FileNotFoundError(executable)
        self.parameters.executable = executable
        self.parameters.args = cmdline[1:]
        self.profile.update_runner(self.runner)
        self.runner.run()

    def __init__(self, profile=None, runner_path=None):
        self.profile = profile
        self.runner = Runner(runner_path)
