
def is_char_valid(c: str) -> bool:
    if 'a' <= c and c <= 'z':
        return True
    if 'A' <= c and c <= 'Z':
        return True
    if '0' <= c and c <= '9':
        return True
    if c == '-' or c == '_' or c == '.' or c == '/':
        return True
    return False


def is_var_name_valid(name: str) -> bool:
    if name == '':
        return False
    if name[0] == '-':
        return False
    for c in name:
        if not is_char_valid(c):
            return False
    return True
