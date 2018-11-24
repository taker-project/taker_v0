import codecs


class ParseError(Exception):
    def __init__(self, row, column, text):
        super().__init__()
        self.row = row
        self.column = column
        self.text = text

    def __str__(self):
        return '{}:{}: error: {}'.format(self.row+1, self.column+1, self.text)


SPACE_CHARS = set([' ', '\t'])
DELIM_CHARS = SPACE_CHARS | set(',:;[]()=')
DELIM_CHARS_TYPE = SPACE_CHARS | set(':=,')
INT_MIN = -(2 ** 63)
INT_MAX = 2 ** 63 - 1


def unescape_str(s):
    return codecs.escape_decode(s.encode())[0].decode()


def skip_spaces(line, pos):
    while (pos < len(line)) and (line[pos] in SPACE_CHARS):
        pos += 1
    return pos


def extract_word(line, pos, delim=DELIM_CHARS):
    pos = skip_spaces(line, pos)
    lpos = pos
    while (pos < len(line)) and (line[pos] not in delim):
        pos += 1
    return (pos, line[lpos:pos])


def extract_string(line, pos):
    pos = skip_spaces(line, pos)
    if pos == len(line) or (line[pos] != '\'' and line[pos] != '\"'):
        raise ParseError(-1, pos, 'expected \' or \"')
    quote = line[pos]
    pos += 1
    lpos = pos
    while pos < len(line):
        if line[pos] == '\\':
            pos += 2
            continue
        if line[pos] == quote:
            return (pos+1, unescape_str(line[lpos:pos]))
        pos += 1
    raise ParseError(-1, pos, 'string is not terminated')


def line_expect(line, pos, c):
    if pos == len(line) or line[pos] != c:
        raise ParseError(-1, pos, '{} expected'.format(repr(c)))
    pos += 1
    return pos


def next_nonspace(line, pos=0):
    pos = skip_spaces(line, pos)
    return '' if pos == len(line) else line[pos]
