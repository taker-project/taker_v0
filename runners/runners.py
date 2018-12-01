from namedlist import namedtuple, namedlist
from enum import Enum
import json
import subprocess
import os
import shutil
import tempfile
from copy import copy

Parameters = namedlist('Parameters',
                       ['time_limit', 'idle_limit', 'memory_limit',
                        'executable', 'clear_env', 'env', 'args',
                        'working_dir', 'stdin_redir', 'stdout_redir',
                        'stderr_redir', 'isolate_dir', 'isolate_policy'])

Results = namedtuple('Results',
                     ['time', 'clock_time', 'memory', 'exitcode', 'signal',
                      'signal_name', 'status', 'comment'])

RunnerInfo = namedtuple('RunnerInfo',
                        ['name', 'description', 'author', 'version',
                         'version_number', 'license', 'features'])


class RunnerFeature(Enum):
    ISOLATE = 'isolate'


class Status(Enum):
    OK = 'ok'
    TIME_LIMIT = 'time-limit'
    IDLE_LIMIT = 'idle-limit'
    MEMORY_LIMIT = 'memory-limit'
    RUNTIME_ERROR = 'runtime-error'
    SECURITY_ERROR = 'security-error'
    RUN_FAIL = 'run-fail'


class IsolatePolicy(Enum):
    NONE = 'none'
    NORMAL = 'normal'
    COMPILE = 'compile'
    STRICT = 'strict'


class RunnerError(Exception):
    pass


def dict_keys_replace(src_dict, src_char, dst_char):
    return dict([(item[0].replace(src_char, dst_char), item[1])
                 for item in src_dict.items()])


def parameters_to_json(parameters):
    param_dict = parameters._asdict()
    param_dict = dict_keys_replace(param_dict, '_', '-')
    if parameters.idle_limit is None:
        param_dict['idle-limit'] = 3.5 * parameters.time_limit
    if parameters.isolate_dir is None:
        param_dict['isolate-dir'] = parameters.working_dir
    if parameters.isolate_policy is None:
        param_dict['isolate-policy'] = IsolatePolicy.NORMAL
    param_dict['isolate-policy'] = param_dict['isolate-policy'].value
    return json.dumps(param_dict)


def typecheck(typename, value):
    if type(value) is not typename:
        raise ValueError('"{}" is not {}'.format(
            str(value), typename.__name__))
    return value


def json_to_runner_info(results_json):
    res = json.loads(results_json)
    res['features'] = set([RunnerFeature(i) for i in res['features']])
    return RunnerInfo(
        name=typecheck(str, res['name']),
        description=typecheck(str, res['description']),
        author=typecheck(str, res['author']),
        version=typecheck(str, res['version']),
        version_number=typecheck(int, res['version-number']),
        license=typecheck(str, res['license']),
        features=res['features'])


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
    def _do_run(self):
        input_str = parameters_to_json(self.parameters)
        try:
            output_str = subprocess.check_output(
                [self.runner_path], input=input_str, universal_newlines=True)
            self.results = json_to_results(output_str)
        except subprocess.CalledProcessError as exc:
            raise RunnerError('runner exited with exitcode = {}'
                              .format(exc.returncode))

    def run(self):
        old_parameters = copy(self.parameters)
        create_temp_dir = (self.pass_stdin or self.capture_stdout
                           or self.capture_stderr)
        if create_temp_dir:
            temp_dir = tempfile.mkdtemp()
        try:
            if self.pass_stdin:
                self.parameters.stdin_redir = os.path.join(temp_dir, 't.in')
                open(self.parameters.stdin_redir, 'w').write(self.stdin)
            if self.capture_stdout:
                self.parameters.stdout_redir = os.path.join(temp_dir, 't.out')
            if self.capture_stderr:
                self.parameters.stderr_redir = os.path.join(temp_dir, 't.err')
            self._do_run()
            try:
                if self.capture_stdout:
                    self.stdout = open(
                        self.parameters.stdout_redir, 'r').read()
                if self.capture_stderr:
                    self.stderr = open(
                        self.parameters.stderr_redir, 'r').read()
            except FileNotFoundError:
                pass
        finally:
            self.parameters = old_parameters
            if create_temp_dir:
                shutil.rmtree(temp_dir)

    def __init__(self, runner_path):
        # TODO : runner must capture stdout instead of creating temp files (?)
        # FIXME : add .exe extension for Windows executables (here on in tests)
        self.runner_path = runner_path
        self.parameters = Parameters(
            time_limit=2.0, idle_limit=None, memory_limit=256.0,
            executable='', clear_env=False, env={}, args=[],
            working_dir='', stdin_redir='', stdout_redir='',
            stderr_redir='', isolate_dir=None, isolate_policy=None)
        self.results = None
        self.pass_stdin = False
        self.capture_stdout = False
        self.capture_stderr = False
        self.stdin = ''
        self.stdout = ''
        self.stderr = ''
