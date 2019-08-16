import sys
from pathlib import Path
import colorama
from colorama import Fore, Style
from compat import fspath
from cli import Subcommand, ConsoleApp, app, register_app
from taskbuilder import RepositoryManager, TaskDirNotFoundError
from invoker import LanguageManager
from runners import Status
from .compiler import CompileError
from .profiled_runner import ProfiledRunner, list_profiles, create_profile
from .cli_base import INVOKER_CMD_NAME


class CompileSubcommand(Subcommand):
    def _update_parser(self, parser):
        super()._update_parser(parser)
        parser.add_argument('src', type=Path,
                            help='Source file to compile')
        parser.add_argument('-o', '--exe', type=Path,
                            help='Output executable')
        parser.add_argument('-l', '--lang', type=str,
                            help='Programming language in use '
                                 '(default: choose by extension)')
        parser.add_argument('-L', '--lib', type=Path, action='append',
                            help='Library to use with the source')

    def run(self, args):
        repo_manager = RepositoryManager()
        language_manager = LanguageManager(repo_manager)

        source = language_manager.create_source(
            args.src, args.exe, args.lang, args.lib)
        try:
            source.compile()
            print(Fore.GREEN + Style.BRIGHT + 'ok' + Style.RESET_ALL)
            print(source.compiler.compiler_output)
        except CompileError as exc:
            print(Fore.RED + Style.BRIGHT + 'compilation error' +
                  Style.RESET_ALL)
            print(source.compiler.compiler_output)
            return exc.exitcode
        return 0

    def __init__(self):
        super().__init__('compile', 'Compile a source file')


class RunSubcommand(Subcommand):
    def _update_parser(self, parser):
        super()._update_parser(parser)
        parser.add_argument('exe', type=Path,
                            help='Executable file to run')
        parser.add_argument('-l', '--lang', type=str,
                            help='Programming language which was used to '
                                 'compile the program (default: treat as '
                                 'independent executable)')
        parser.add_argument('-w', '--work-dir', type=Path,
                            help='Working directory for the program '
                                 '(default: depends on profile)')
        parser.add_argument('-q', '--quiet', action='store_true',
                            help='Enable quiet mode')
        parser.add_argument('-i', '--input', type=str, default='',
                            help='Standard input to pass to the program')
        parser.add_argument('-p', '--profile', type=str, required=True,
                            choices=list_profiles(),
                            help='Profile used to run the program')
        parser.add_argument('args', nargs='*', type=str,
                            help='Arguments to pass to the program')

    def run(self, args):
        repo_manager = RepositoryManager()
        language_manager = LanguageManager(repo_manager)

        profile = create_profile(args.profile, repo_manager.repo)
        runner = ProfiledRunner(profile)

        cmdline = []
        if args.lang is None:
            cmdline = [fspath(args.exe.absolute())] + args.args
        else:
            lang = language_manager.get_lang(args.lang)
            cmdline = lang.run_args(args.exe, args.args)

        if args.input is not None:
            runner.stdin = args.input

        runner.run(cmdline, args.work_dir)
        if args.quiet:
            print(runner.stdout, end='')
            print(runner.stderr, end='', file=sys.stderr)
            status = runner.results.status
            if status not in {Status.OK, Status.RUNTIME_ERROR}:
                print(Fore.RED + Style.BRIGHT + 'error: ' + Style.RESET_ALL +
                      'program exited with status ' + repr(status),
                      file=sys.stderr)
        else:
            print(runner.format_results())
        return runner.get_cli_exitcode()

    def __init__(self):
        super().__init__('run', 'Run a compiled program')


class InvokerApp(ConsoleApp):
    def run(self, args=None):
        try:
            super().run(args)
        except TaskDirNotFoundError:
            self.error('you must be in task directory')

    def __init__(self):
        super().__init__(INVOKER_CMD_NAME)
        self.parser.description = \
            'Compiles and runs source codes'


def main():
    register_app(InvokerApp())
    colorama.init()
    app().add_subcommand(CompileSubcommand())
    app().add_subcommand(RunSubcommand())
    app().run()
