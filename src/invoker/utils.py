import os


def is_valid_ext(ext):
    if ext == '':
        return True
    return ext.startswith('.')


def default_exe_ext():
    return '.exe' if os.name == 'nt' else ''
