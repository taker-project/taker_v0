import shutil
import sys
import pytest
from compat import fspath
from cli import *
from cli import consoleapp
from ...pytest_fixtures import taker_app


class MySubcommand(Subcommand):
    def _update_parser(self, parser):
        parser.add_argument('value', type=int, default=0)

    def run(self, args):
        return self.callback(args.value)

    def __init__(self, callback):
        super().__init__('cmd', 'Just a command', ['c', 'cm'])
        self.callback = callback


def test_mock_app_exe(taker_app):
    assert taker_app == app_exe()
    assert fspath(app_exe()) == shutil.which('take')


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
        with pytest.raises(RuntimeError):
            app_exe('taker2')

        got_value = 0

        def callback(value):
            nonlocal got_value
            got_value = value
            return 142

        my_app.add_subcommand(MySubcommand(callback))
        with pytest.raises(SystemExit) as exc:
            my_app.run(['cmd', '42'])
        assert exc.value.code == 142
        assert got_value == 42
    finally:
        consoleapp.__APP = old_app
