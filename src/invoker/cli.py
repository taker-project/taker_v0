from pathlib import Path
from colorama import Fore, Style
from cli import Subcommand
from taskbuilder import TaskManager
from invoker import LanguageManager
from .compiler import CompileError
from .sourcecode import SourceCode


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
        # TODO: create global manager to initialize everything
        # in one command (?)
        self.task_manager = TaskManager()
        self.language_manager = LanguageManager(self.task_manager.repo)

        language = None
        if args.lang is not None:
            language = self.language_manager.get_lang(args.lang)
        source = self.language_manager.create_source(
            args.src, args.exe, language, args.lib)
        try:
            source.compile()
            print(f'{Fore.GREEN}{Style.BRIGHT}ok{Style.RESET_ALL}')
            print(source.compiler.compiler_output)
        except CompileError as exc:
            print(f'{Fore.RED}{Style.BRIGHT}compilation error'
                  f'{Style.RESET_ALL}')
            print(source.compiler.compiler_output)
        return 0

    def __init__(self):
        super().__init__('compile', 'Compile a source file')
