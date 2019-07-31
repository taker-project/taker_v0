from cli import ConsoleApp, app, register_app


class TakerApp(ConsoleApp):
    def __init__(self):
        super().__init__('take')
        self.parser.description = \
            'Taker - a task preparation system for competitive programming'


register_app(TakerApp())


def main():
    app().run()
