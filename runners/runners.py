from namedlist import namedtuple, namedlist
from enum import Enum
import json
import subprocess

Parameters = namedlist('Parameters',
                       ['time_limit', 'idle_limit', 'memory_limit',
                        'executable', 'clear_env', 'env', 'args',
                        'working_dir', 'stdin_redir', 'stdout_redir',
                        'stderr_redir'])

Results = namedtuple('Results',
                     ['time', 'clock_time', 'memory', 'exitcode', 'signal',
                      'signal_name', 'status', 'comment'])


class Status(Enum):
    OK = 'ok'
    TIME_LIMIT = 'time-limit'
    IDLE_LIMIT = 'idle-limit'
    MEMORY_LIMIT = 'memory-limit'
    RUNTIME_ERROR = 'runtime-error'
    SECURITY_ERROR = 'security-error'
    RUN_FAIL = 'run-fail'


class RunnerError(Exception):
    pass


def dict_keys_replace(src_dict, src_char, dst_char):
    return dict([(item[0].replace(src_char, dst_char), item[1])
                 for item in src_dict.items()])


def parameters_to_json(parameters):
    if parameters.idle_limit is None:
        parameters.idle_limit = 3.5 * parameters.time_limit
    param_dict = parameters._asdict()
    param_dict = dict_keys_replace(param_dict, '_', '-')
    return json.dumps(param_dict)


def typecheck(typename, value):
    if type(value) is not typename:
        raise ValueError('"{}" is not {}'.format(
            str(value), typename.__name__))
    return value


def json_to_results(results_json):
    # when time is string but it's convertible to float
    # then it passes validation
    # FIXME : fail validation in this cases (?)
    res = json.loads(results_json)
    return Results(
        time=float(res['time']),
        clock_time=float(res['clock-time']),
        memory=float(res['memory']),
        exitcode=typecheck(int, res['exitcode']),
        signal=typecheck(int, res.setdefault('signal', 0)),
        signal_name=typecheck(str, res.setdefault('signal-name', '')),
        status=Status(res['status']),
        comment=typecheck(str, res.setdefault('comment', '')))


class Runner:
    def run(self):
        input_str = parameters_to_json()
        try:
            output_str = subprocess.check_output(
                [self.runner_path], input=input_str, universal_newlines=True)
        except subprocess.CalledProcessError as exc:
            raise RunnerError('runner exited with exitcode = {}'
                              .format(exc.returncode))

    def __init__(self, runner_path):
        self.runner_path = runner_path
        self.parameters = Parameters(
            time_limit=2.0, idle_limit=None, memory_limit=256.0,
            executable='', clear_env=False, env={}, args=[],
            working_dir='', stdin_redir='', stdout_redir='',
            stderr_redir='')
        self.results = None
