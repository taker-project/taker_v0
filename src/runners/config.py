from configs import manager

DEFAULT_CONFIG = '''[path]
# Runner executable (if null or unset, use default)
# executable = 'taker_unixrun'
'''

CONFIG_NAME = 'runner'


def config():
    return manager.request(CONFIG_NAME, DEFAULT_CONFIG)
