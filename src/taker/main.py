import colorama
from cli import app, register_app
from .cmd_taskbuilder import InitSubcommand, BuildSubcommand
from .taker_app import TakerApp


def main():
    register_app(TakerApp())
    colorama.init()
    app().add_subcommand(InitSubcommand())
    app().add_subcommand(BuildSubcommand())
    app().run()
