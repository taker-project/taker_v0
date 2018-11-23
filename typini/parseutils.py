from typing import *  # type: ignore
import codecs


class ParseError(Exception):
    def __init__(self, row: int, column: int, text: str):
        super().__init__()
        self.row = row
        self.column = column
        self.text = text

    def __str__(self) -> str:
        return '{}:{}: error: {}'.format(self.row+1, self.column+1, self.text)


SPACE_CHARS = set([' ', '\t'])
DELIM_CHARS = SPACE_CHARS | set(',:;[]()=')
DELIM_CHARS_TYPE = SPACE_CHARS | set(':=,')
INT_MIN = -(2 ** 63)
INT_MAX = 2 ** 63 - 1


def unescape_str(s: str) -> str:
    # TODO : Remove this hack and add something better!
    return bytes(s, 'utf8').decode('unicode_escape').encode('latin1').decode()


def skip_spaces(line: str, pos: int) -> int:
    while (pos < len(line)) and (line[pos] in SPACE_CHARS):
        pos += 1
    return pos


def extract_word(line: str,
                 pos: int,
                 delim: Set[str] = DELIM_CHARS) -> Tuple[int, str]:
    pos = skip_spaces(line, pos)
    lpos = pos
    while (pos < len(line)) and (line[pos] not in delim):
        pos += 1
    return (pos, line[lpos:pos])


def extract_string(line: str, pos: int) -> Tuple[int, str]:
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


def line_expect(line: str, pos: int, c: str) -> int:
    if pos == len(line) or line[pos] != c:
        raise ParseError(-1, pos, '{} expected'.format(repr(c)))
    pos += 1
    return pos


def next_nonspace(line: str, pos: int = 0) -> str:
    pos = skip_spaces(line, pos)
    return '' if pos == len(line) else line[pos]
