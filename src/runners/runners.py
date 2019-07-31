from enum import Enum
import json
import subprocess
import os
import shutil
import tempfile
from colorama import Fore, Style
from copy import copy
from collections import namedtuple
from .config import config
from compat import fspath
from pathlib import Path

# TODO : the module architecture is not flexible enough, rewrite it!


class Parameters:
    def __defaults(self):
        return {
            'time_limit': 2.0,
            'idle_limit': None,
            'memory_limit': 256.0,
            'executable': '',
            'clear_env': False,
            'env': {},
            'args': [],
            'working_dir': '',
            'stdin_redir': '',
            'stdout_redir': '',
            'stderr_redir': '',
            'isolate_dir': None,
            'isolate_policy': None
        }

    def _asdict(self):
        return vars(self)

    def __init__(self, **kwargs):
        defaults = self.__defaults()
        for item in kwargs:
            if item not in defaults:
                raise KeyError(item)
        self.__dict__.update(defaults)
        self.__dict__.update(kwargs)


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

    def __repr__(self):
        return STATUS_COLORS[self] + Style.BRIGHT + \
               self.value + Style.RESET_ALL


STATUS_COLORS = {
    Status.OK: Fore.GREEN,
    Status.TIME_LIMIT: Fore.BLUE,
    Status.IDLE_LIMIT: Fore.BLUE,
    Status.MEMORY_LIMIT: Fore.CYAN,
    Status.RUNTIME_ERROR: Fore.MAGENTA,
    Status.SECURITY_ERROR: '',
    Status.RUN_FAIL: ''
}


class IsolatePolicy(Enum):
    NONE = 'none'
    NORMAL = 'normal'
    COMPILE = 'compile'
    STRICT = 'strict'


class RunnerError(Exception):
    pass


def dict_keys_replace(src_dict, src_char, dst_char):
    return {item[0].replace(src_char, dst_char): item[1]
            for item in src_dict.items()}


def parameters_to_json(parameters):
    param_dict = parameters._asdict()
    param_dict = dict_keys_replace(param_dict, '_', '-')
    # convert paths to strings
    for key in param_dict:
        if isinstance(param_dict[key], Path):
            param_dict[key] = fspath(param_dict[key])
    # set default values (if unset)
    if parameters.idle_limit is None:
        param_dict['idle-limit'] = 3.5 * parameters.time_limit
    if parameters.isolate_dir is None:
        param_dict['isolate-dir'] = parameters.working_dir
    if parameters.isolate_policy is None:
        param_dict['isolate-policy'] = IsolatePolicy.NORMAL
    param_dict['isolate-policy'] = param_dict['isolate-policy'].value
    # dump as JSON
    return json.dumps(param_dict)


def typecheck(typename, value):
    if not isinstance(value, typename):
        raise ValueError('"{}" is not {}'.format(
            str(value), typename.__name__))
    return value


def json_to_runner_info(results_json):
    res = json.loads(results_json)
    res['features'] = {RunnerFeature(i) for i in res['features']}
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
    def get_runner_info(self):
        # FIXME : do not call runner process for each instance (?)
        return json_to_runner_info(
            subprocess.check_output([self.runner_path, '-?'],
                                    input='', universal_newlines=True))

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
        self.results = None
        self.stdout = ''
        self.stderr = ''
        create_temp_dir = (self.pass_stdin or self.capture_stdout
                           or self.capture_stderr)
        if create_temp_dir:
            temp_dir = tempfile.mkdtemp()
        try:
            if self.pass_stdin:
                self.parameters.stdin_redir = os.path.join(temp_dir, 't.in')
                open(self.parameters.stdin_redir, 'w',
                     encoding='utf8').write(self.stdin)
            if self.capture_stdout:
                self.parameters.stdout_redir = os.path.join(temp_dir, 't.out')
            if self.capture_stderr:
                self.parameters.stderr_redir = os.path.join(temp_dir, 't.err')
            self._do_run()
            try:
                if self.capture_stdout:
                    self.stdout = open(
                        self.parameters.stdout_redir, 'r',
                        encoding='utf8').read()
                if self.capture_stderr:
                    self.stderr = open(
                        self.parameters.stderr_redir, 'r',
                        encoding='utf8').read()
            except FileNotFoundError:
                pass
        finally:
            self.parameters = old_parameters
            if create_temp_dir:
                shutil.rmtree(temp_dir)

    def __init__(self, runner_path=None):
        # TODO : runner must capture stdout instead of creating temp files (?)
        # FIXME : add .exe extension for Windows executables (here + in tests)
        if runner_path is None:
            runner_path = config()['path'].get('executable')
        if runner_path is None:
            # FIXME: add better runner detection
            runner_path = shutil.which('taker_unixrun')
        if runner_path is None:
            raise RunnerError('runner executable not found')
        self.runner_path = runner_path
        self.parameters = Parameters()
        self.results = None
        self.pass_stdin = False
        self.capture_stdout = False
        self.capture_stderr = False
        self.stdin = ''
        self.stdout = ''
        self.stderr = ''
        self.info = self.get_runner_info()
