from argparse import ArgumentParser
import sys


class SubcommandError(Exception):
    pass


class Subcommand:
    @property
    def parser(self):
        return self.__parser

    @parser.setter
    def parser(self, value):
        if self.parser is not None:
            raise SubcommandError('parser can be set only once')
        self.__parser = value
        self.parser.set_defaults(func=(lambda args: sys.exit(self.run(args))))
        self._update_parser(self.__parser)

    def _update_parser(self, parser):
        pass

    def run(self, args):
        return 0

    def __init__(self, name, help='', aliases=None):
        self.name = name
        self.help = help
        self.aliases = aliases if aliases else []
        self.__parser = None


class ConsoleApp:
    def add_subcommand(self, subcmd):
        subcmd_parser = self.subparsers.add_parser(subcmd.name,
                                                   help=subcmd.help,
                                                   aliases=subcmd.aliases)
        subcmd.parser = subcmd_parser

    def run(self, args=None):
        p_args = self.parser.parse_args(args)
        p_args.func(p_args)
        raise RuntimeError('program must finish after calling appropriate '
                           'command, but that didn\'t happen. Seems to be '
                           'a bug :(')

    def __init__(self, name):
        self.name = name
        self.parser = ArgumentParser(prog=name)
        self.subparsers = self.parser.add_subparsers(metavar='',
                                                     required=True,
                                                     title='subcommands')


__APP = None


def app():
    if __APP is None:
        raise RuntimeError('app is not initialised')
    return __APP


def register_app(app):
    global __APP
    if __APP is not None:
        raise RuntimeError('app is already initialised')
    __APP = app
