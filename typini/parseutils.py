import codecs


class TypiniError(Exception):
    pass


class ParseError(TypiniError):
    def __init__(self, row, column, text):
        super().__init__()
        self.row = row
        self.column = column
        self.text = text
        self.filename = None

    def __str__(self):
        res = '{}:{}: error: {}'.format(self.row+1, self.column+1, self.text)
        if self.filename is not None:
            res = str(self.filename) + ':' + res
        return res


SPACE_CHARS = set([' ', '\t'])
DELIM_CHARS = SPACE_CHARS | set(',:;[]()=')
DELIM_CHARS_TYPE = SPACE_CHARS | set(':=,')
INT_MIN = -(2 ** 63)
INT_MAX = 2 ** 63 - 1


def unescape_str(string):
    return codecs.escape_decode(string.encode())[0].decode()


def skip_spaces(line, pos):
    while (pos < len(line)) and (line[pos] in SPACE_CHARS):
        pos += 1
    return pos


def extract_word(line, pos, delim=DELIM_CHARS):
    pos = skip_spaces(line, pos)
    lpos = pos
    while (pos < len(line)) and (line[pos] not in delim):
        pos += 1
    return (pos, lpos, line[lpos:pos])


def extract_string(line, pos):
    pos = skip_spaces(line, pos)
    if pos == len(line) or (line[pos] != '\'' and line[pos] != '\"'):
        raise ParseError(-1, pos, '\' or \" expected')
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


def line_expect(line, pos, char):
    if pos == len(line) or line[pos] != char:
        raise ParseError(-1, pos, '{} expected'.format(repr(char)))
    pos += 1
    return pos


def next_nonspace(line, pos=0):
    pos = skip_spaces(line, pos)
    return '' if pos == len(line) else line[pos]
