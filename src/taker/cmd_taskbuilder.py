from pathlib import Path
from cli import Subcommand, app
from .global_state import GlobalState

# FIXME : write tests for these commands


class InitSubcommand(Subcommand):
    def _update_parser(self, parser):
        super()._update_parser(parser)

    def run(self, args):
        gs = GlobalState(task_dir=Path.cwd())
        gs.repo_manager.init_task()
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
        gs = GlobalState()
        if args.jobs is not None:
            if args.jobs < 0 or args.jobs > 512:
                app().error('number of jobs must be between 0 and 512')
        gs.repo_manager.build(args.target, args.jobs)
        return 0

    def __init__(self):
        super().__init__('build', 'Build the task')
