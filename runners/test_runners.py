import json
import os
from os import path
import tempfile
import pytest
from runners.runners import *


def test_parameters_to_json():
    parameters = Parameters(
        time_limit=1.0,
        idle_limit=None,
        memory_limit=256.0,
        executable='exe',
        clear_env=False,
        env={'ENV1': '4', 'ENV2': '5'},
        args=['arg1', 'arg2'],
        working_dir='work',
        stdin_redir='in.txt',
        stdout_redir='out.txt',
        stderr_redir='err.txt',
        isolate_dir=None,
        isolate_policy=None
    )
    assert (json.loads(parameters_to_json(parameters)) ==
            {
                'time-limit': 1.0,
                'idle-limit': 3.5,
                'memory-limit': 256.0,
                'executable': 'exe',
                'clear-env': False,
                'env': {'ENV1': '4', 'ENV2': '5'},
                'args': ['arg1', 'arg2'],
                'working-dir': 'work',
                'stdin-redir': 'in.txt',
                'stdout-redir': 'out.txt',
                'stderr-redir': 'err.txt',
                'isolate-dir': 'work',
                'isolate-policy': 'normal'
    })


def test_results_from_json():
    src_dict = {'time': 2.5, 'clock-time': 3, 'memory': 42.0, 'exitcode': 10,
                'status': 'ok'}
    assert (json_to_results(json.dumps(src_dict)) ==
            Results(time=2.5, clock_time=3.0, memory=42.0, exitcode=10,
                    signal=0, signal_name='', status=Status.OK, comment=''))

    src_dict['signal'] = 42
    src_dict['comment'] = '!'
    assert (json_to_results(json.dumps(src_dict)) ==
            Results(time=2.5, clock_time=3.0, memory=42.0, exitcode=10,
                    signal=42, signal_name='', status=Status.OK, comment='!'))

    def invoke_value_error(key, value):
        old_value = src_dict[key]
        src_dict[key] = value
        with pytest.raises(ValueError):
            json_to_results(json.dumps(src_dict))
        src_dict[key] = old_value

    invoke_value_error('time', 'hello')
    invoke_value_error('clock-time', 'hello')
    invoke_value_error('memory', 'hello')
    invoke_value_error('exitcode', 1.2)
    invoke_value_error('signal', 1.2)
    invoke_value_error('status', 'invalid')
    invoke_value_error('comment', 42)


def test_runner_info_from_json():
    src_dict = {'name': 'myName', 'description': 'myDescr', 'author': 'me',
                'version': '1.2.3', 'version-number': 42, 'license': 'GPL-3+',
                'features': ['isolate']}
    assert (json_to_runner_info(json.dumps(src_dict)) ==
            RunnerInfo(name='myName', description='myDescr', author='me',
                       version='1.2.3', version_number=42, license='GPL-3+',
                       features=set([RunnerFeature.ISOLATE])))


def do_runner_test(runner_name):
    tests_location = path.realpath(path.join('runners', 'tests', 'build'))
    runner_path = path.realpath(path.join('runners', 'taker_unixrun',
                                          'build', runner_name))

    # basic test: check if program prints some output
    runner = Runner(runner_path)
    runner.capture_stdout = True
    runner.parameters.executable = path.join(tests_location, 'basic_test')
    runner.run()
    assert runner.results.status == Status.OK
    assert runner.stdout == 'hello world\n'

    # invalid test: check for RUN_FAIL for non-existing executables
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(tests_location, 'invalid_test')
    runner.run()
    assert runner.results.status == Status.RUN_FAIL

    # sleepy test: check for IDLE_LIMIT
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(tests_location, 'sleepy_test')
    runner.parameters.idle_limit = 0.5
    runner.run()
    assert runner.results.status == Status.IDLE_LIMIT
    runner.parameters.idle_limit = 0.7
    runner.run()
    assert runner.results.status == Status.OK
    assert abs(runner.results.clock_time - 0.55) < 0.02
    assert runner.results.time < 0.02

    # worky test: check for TIME_LIMIT
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(tests_location, 'worky_test')
    runner.parameters.time_limit = 0.5
    runner.run()
    assert runner.results.status == Status.TIME_LIMIT
    runner.parameters.time_limit = 0.7
    runner.run()
    assert runner.results.status == Status.OK
    assert abs(runner.results.time - 0.55) < 0.02

    # memory_test: check for MEMORY_LIMIT
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(tests_location, 'memory_test')
    # on taker_unixrun, this test fail with RUNTIME_ERROR
    # FIXME : better detect MEMORY_LIMIT and RUNTIME_ERROR for unixrun!
    if runner_name not in set(['taker_unixrun']):
        runner.parameters.memory_limit = 20.0
        runner.run()
        assert runner.results.status == Status.MEMORY_LIMIT
    runner.parameters.memory_limit = 40.0
    runner.run()
    assert runner.results.status == Status.MEMORY_LIMIT
    runner.parameters.memory_limit = 256.0
    runner.run()
    assert runner.results.status == Status.OK
    assert runner.results.memory >= 59.0
    assert runner.results.memory <= 69.0

    # vector_test: another memory test, now with vectors
    # memory allocations and deallocations are very fast here
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(tests_location, 'vector_test')
    if runner_name not in set(['taker_unixrun']):
        runner.parameters.memory_limit = 20.0
        runner.run()
        assert runner.results.status == Status.MEMORY_LIMIT
    runner.parameters.memory_limit = 40.0
    runner.run()
    assert runner.results.status == Status.MEMORY_LIMIT
    runner.parameters.memory_limit = 128.0
    runner.run()
    assert runner.results.status == Status.OK
    assert runner.results.memory >= 59.0
    assert runner.results.memory <= 69.0

    # vector_pushback_test: memory tests with push_back() into vector
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(
        tests_location, 'vector_pushback_test')
    runner.parameters.memory_limit = 40.0
    runner.run()
    assert runner.results.status == Status.MEMORY_LIMIT
    runner.parameters.memory_limit = 150.0
    runner.parameters.time_limit = 6.0
    runner.run()
    runner.parameters.time_limit = 2.0
    assert runner.results.status == Status.OK
    assert runner.results.memory >= 59.0

    # alloc1_test: fast allocation/deallocation
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(
        tests_location, 'alloc1_test')
    runner.run()
    assert runner.results.memory >= 59.0
    assert runner.results.memory <= 69.0

    # alloc2_test: fast allocation/deallocation
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(
        tests_location, 'alloc2_test')
    runner.run()
    assert runner.results.memory >= 19.0
    assert runner.results.memory <= 29.0

    # env_test: test for env and clear_env parameters
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(
        tests_location, 'env_test')
    runner.capture_stdout = True
    runner.run()
    assert runner.stdout == 'none\n'
    runner.parameters.env['HELLO'] = '42'
    runner.run()
    assert runner.stdout == '42\n'
    os.environ['HELLO'] = 'world'
    runner.run()
    assert runner.stdout == '42\n'
    runner.parameters.env.pop('HELLO')
    runner.run()
    assert runner.stdout == 'world\n'
    runner.parameters.clear_env = True
    runner.run()
    assert runner.stdout == 'none\n'
    runner.parameters.env['HELLO'] = '42'
    runner.run()
    assert runner.stdout == '42\n'
    os.environ.pop('HELLO')

    # runerror_test: test for RUNTIME_ERROR (both by exitcode and signal)
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(
        tests_location, 'runerror_test')
    runner.pass_stdin = True
    runner.stdin = 'normal'
    runner.run()
    assert runner.results.status == Status.OK
    runner.stdin = 'assert'
    runner.run()
    assert runner.results.status == Status.RUNTIME_ERROR
    runner.stdin = 'error'
    runner.run()
    assert runner.results.status == Status.RUNTIME_ERROR
    runner.pass_stdin = False

    # args_test: test for args parameter
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(
        tests_location, 'args_test')
    runner.capture_stdout = True
    runner.parameters.args = ['arg1', 'arg2']
    runner.run()
    assert runner.stdout == 'arg1\narg2\n'
    runner.parameters.args = []
    runner.capture_stdout = False

    # broken_test: test for RUN_FAIL on bad executables
    runner = Runner(runner_path)
    runner.parameters.executable = path.join(
        tests_location, 'broken_test')
    runner.run()
    assert runner.results.status == Status.RUN_FAIL


def test_unixrun():
    do_runner_test('taker_unixrun')
