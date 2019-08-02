import pytest
from invoker.profiled_runner import *
from invoker.config import CONFIG_NAME
from runners import Runner
from ...pytest_fixtures import *


class CustomRunProfile(ConfigRunProfile):
    @staticmethod
    def name():
        return 'custom'


def test_profiles(config_manager, task_manager, monkeypatch, taker_app):
    config_manager.user_config(CONFIG_NAME).open(
        'w', encoding='utf8').write('''
[compiler]
time-limit = 3.0
memory-limit = 100.0

[checker]
time-limit = 6.0
memory-limit = 200.0

[validator]
time-limit = 9.0
memory-limit = 300.0

[generator]
time-limit = 12.0
memory-limit = 400.0

[custom]
time-limit = 15.0
memory-limit = 500.0
''')

    runner = Runner()
    repo = task_manager.repo

    compiler_profile = create_profile('compiler', repo)
    assert type(compiler_profile) is CompilerRunProfile
    compiler_profile.update_runner(runner)
    assert runner.parameters.time_limit == 3.0
    assert runner.parameters.memory_limit == 100.0

    checker_profile = create_profile('checker', repo)
    assert type(checker_profile) is CheckerRunProfile
    checker_profile.update_runner(runner)
    assert runner.parameters.time_limit == 6.0
    assert runner.parameters.memory_limit == 200.0

    validator_profile = create_profile('validator', repo)
    assert type(validator_profile) is ValidatorRunProfile
    validator_profile.update_runner(runner)
    assert runner.parameters.time_limit == 9.0
    assert runner.parameters.memory_limit == 300.0

    generator_profile = create_profile('generator', repo)
    assert type(generator_profile) is GeneratorRunProfile
    generator_profile.update_runner(runner)
    assert runner.parameters.time_limit == 12.0
    assert runner.parameters.memory_limit == 400.0

    with pytest.raises(KeyError):
        create_profile('custom', repo)

    register_profile(CustomRunProfile)
    custom_profile = create_profile('custom', repo)
    assert type(custom_profile) is CustomRunProfile
    custom_profile.update_runner(runner)
    assert runner.parameters.time_limit == 15.0
    assert runner.parameters.memory_limit == 500.0

    run_count = 0

    def run(self):
        nonlocal run_count
        run_count += 1

    monkeypatch.setattr(Runner, 'run', run)
    profiled_runner = ProfiledRunner(generator_profile)
    profiled_runner.stdin = 'some input'
    in_runner = profiled_runner._ProfiledRunner__runner
    profiled_runner.run([taker_app])
    assert run_count == 1
    assert in_runner.parameters.time_limit == 12.0
    assert in_runner.parameters.memory_limit == 400.0
    assert not in_runner.pass_stdin
    assert not in_runner.capture_stdout
    assert in_runner.capture_stderr
    assert in_runner.stdin == 'some input'
    assert in_runner.stdin == profiled_runner.stdin
