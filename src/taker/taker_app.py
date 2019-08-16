from cli import ConsoleApp, app
from taskbuilder import TaskDirNotFoundError


class TakerApp(ConsoleApp):
    def run(self, args=None):
        try:
            super().run(args)
        except TaskDirNotFoundError:
            self.error('you must be in task directory')

    def __init__(self):
        super().__init__('take')
        self.parser.description = \
            'Taker - a task preparation system for competitive programming'
