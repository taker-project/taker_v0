from .runners import *
import json
import pytest


def test_parameters_to_json():
    parameters = Parameters(
        time_limit=1.0, idle_limit=None, memory_limit=256.0, executable='exe',
        clear_env=False, env={'ENV1': '4', 'ENV2': '5'}, args=['arg1', 'arg2'],
        working_dir='work', stdin_redir='in.txt', stdout_redir='out.txt',
        stderr_redir='err.txt')
    assert (parameters_to_json(parameters) == '{"time-limit": 1.0, '
            '"idle-limit": 3.5, "memory-limit": 256.0, "executable": "exe", '
            '"clear-env": false, "env": {"ENV1": "4", "ENV2": "5"}, "args": '
            '["arg1", "arg2"], "working-dir": "work", "stdin-redir": '
            '"in.txt", "stdout-redir": "out.txt", "stderr-redir": "err.txt"}')


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
