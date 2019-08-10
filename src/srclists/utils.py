import os
from typini import is_var_name_valid


def is_char_valid(ch):
    if 'a' <= ch and ch <= 'z':
        return True
    if 'A' <= ch and ch <= 'Z':
        return True
    if '0' <= ch and ch <= '9':
        return True
    if ch in ('-', '_', '.', '+'):
        return True


def is_filename_valid(filename):
    if not is_var_name_valid(filename):
        return False
    if not filename:
        return False
    for ch in filename:
        if not is_char_valid(ch):
            return False
    if filename[0] in ('.', '-'):
        return False
    if filename.count('.') > 1:
        return False
    root_part = os.path.splitext(filename)
    if root_part[0] in ('Makefile', 'Takefile'):
        return False
    return True
