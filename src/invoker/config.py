from configs import manager

DEFAULT_CONFIG = '''[compile]
# Compilation time (in seconds)
time-limit: float = 30.0
# Compilation memory limits (in MBytes)
memory-limit: float = 512.0

# You can define your own languages here:
# Example:
# [lang/cpp.mygcc]
# compile-args = ['g++', '{src}', '-o', '{exe}', '-O2', '-I{lib}']
# run-args = ['{exe}']
# priority = 0

# To disable the existing one, use
# [lang/c++.gcc]
# active = false
'''

CONFIG_NAME = 'taskbuilder'


def config():
    if CONFIG_NAME not in manager:
        manager.add_default(CONFIG_NAME, DEFAULT_CONFIG)
    return manager[CONFIG_NAME]
