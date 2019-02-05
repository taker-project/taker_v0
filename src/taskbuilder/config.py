from configs import manager

DEFAULT_CONFIG = '''[make]
# Number of jobs for make.
# If set to null, the number of processor cores is used.
jobs: int = null
'''

CONFIG_NAME = 'taskbuilder'


def config():
    if CONFIG_NAME not in manager:
        manager.add_default(CONFIG_NAME, DEFAULT_CONFIG)
    return manager[CONFIG_NAME]
