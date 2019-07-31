from compat import fspath
from cli import *
import cli.consoleapp
import shutil
import pytest
import sys
from unittest import mock


class MySubcommand(Subcommand):
    def _update_parser(self, parser):
        parser.add_argument('value', type=int, default=0)

    def run(self, args):
        return self.callback(args.value)

    def __init__(self, callback):
        super().__init__('cmd', 'Just a command', ['c', 'cm'])
        self.callback = callback


def test_app():
    old_app = consoleapp.__APP
    try:
        consoleapp.__APP = None
        with pytest.raises(RuntimeError):
            app()

        my_app = ConsoleApp('take')
        register_app(my_app)
        assert consoleapp.__APP is my_app
        with pytest.raises(RuntimeError):
            register_app(ConsoleApp('taker2'))
        assert consoleapp.__APP is my_app

        exe = app_exe()
        assert fspath(exe) == shutil.which('take')

        got_value = 0

        def callback(value):
            nonlocal got_value
            got_value = 42
            return 3

        with mock.patch('sys.exit'):
            my_app.add_subcommand(MySubcommand(callback))
            with pytest.raises(RuntimeError) as exc:
                my_app.run(['cmd', '42'])
            assert exc.value.args[0].startswith('program must finish after ')
            sys.exit.assert_called_once_with(3)
            assert got_value == 42
    finally:
        consoleapp.__APP = old_app
