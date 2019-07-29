
def is_char_valid(char):
    if 'a' <= char and char <= 'z':
        return True
    if 'A' <= char and char <= 'Z':
        return True
    if '0' <= char and char <= '9':
        return True
    if char in ('+', '-', '_', '.', '/'):
        return True
    return False


def is_var_name_valid(name):
    if name == '':
        return False
    if name[0] == '-':
        return False
    for char in name:
        if not is_char_valid(char):
            return False
    return True
