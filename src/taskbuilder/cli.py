from pathlib import Path
from cli import Subcommand, app
from .manager import RepositoryManager

# TODO: move these commands to some other place (?)


class InitSubcommand(Subcommand):
    def _update_parser(self, parser):
        super()._update_parser(parser)

    def run(self, args):
        manager = RepositoryManager(task_dir=Path.cwd())
        return 0

    def __init__(self):
        super().__init__('init', 'Initialize the task directory')


class BuildSubcommand(Subcommand):
    def _update_parser(self, parser):
        super()._update_parser(parser)
        parser.add_argument('target', nargs='?', type=str,
                            help='Target ot build (default: build everything)')
        parser.add_argument('-j', '--jobs', type=int,
                            help='Number of jobs to run in parallel')

    def run(self, args):
        if args.jobs is not None:
            if args.jobs < 0 or args.jobs > 512:
                app().error('number of jobs must be between 0 and 512')
        print(args)
        # TODO
        return 0

    def __init__(self):
        super().__init__('build', 'Build the task')
