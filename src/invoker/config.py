from configs import manager

DEFAULT_CONFIG = '''[compiler]
# Compilation time (in seconds)
time-limit: float = 30.0
# Compilation memory limits (in MBytes)
memory-limit: float = 512.0

# You can set time/memory limit for other executables here
[checker]
time-limit: float = 10.0
memory-limit: float = 512.0

[validator]
time-limit: float = 10.0
memory-limit: float = 512.0

[generator]
time-limit: float = 10.0
memory-limit: float = 512.0

# You can define your own languages here:
# Example:
# [lang/cpp.mygcc]
# compile-args = ['g++', '{src}', '-o', '{exe}', '-O2', '-I{lib}']
# run-args = ['{exe}']
# priority = 0
# exe-ext = '.myexe'

# To disable the existing one, use
# [lang/c++.gcc]
# active = false
'''

CONFIG_NAME = 'invoker'


def config():
    return manager.request(CONFIG_NAME, DEFAULT_CONFIG)
