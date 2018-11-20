from .names import *
from .parseutils import *


class EmptyNode:
    def load(self, line, pos=0):
        skip_spaces(line, pos)
        if pos == len(line):
            return
        if line[pos] != '#':
            raise ParseError(-1, pos, 'comment expected')
        self.comment = line[pos+1:]
        return len(line)

    def save(self, line=''):
        if line != '':
            line += ' '
        line += '#' + self.comment
        return line

    def __init__(self, comment=''):
        self.comment = comment


class VariableValue:
    def _do_validate(self):
        if self.value is None:
            return True
        return type(self.value) == self.var_type()

    def var_type(self):
        raise NotImplementedError()

    def validate(self):
        if not self._do_validate():
            raise TypeError('{} contains an invalid value'
                            .format(type(self).__name__))

    def _do_load(self, line, pos=0):
        raise NotImplementedError()

    def load(self, line, pos=0):
        new_pos, word = extract_word(line, pos)
        if word == 'null':
            self.value = None
            return new_pos
        return self._do_load(line, pos)

    def _do_save(self):
        return str(self.value)

    def save(self):
        self.validate()
        if self.value is None:
            return 'null'
        return self._do_save()

    def __init__(self, value=None):
        self.value = value


class NumberValue(VariableValue):
    def _do_load(self, line, pos=0):
        pos, word = extract_word(line, pos)
        try:
            self.value = self.var_type()(word)
            self.validate()
        except TypeError:
            raise ParseError(-1, pos, '{} expected, {} found'
                             .format(self.var_type().__name__,
                                     word))
        return pos


class IntValue(NumberValue):
    def var_type(self):
        return int

    def _do_validate(self):
        if type(self.value) is int:
            return INT_MIN <= self.value and self.value <= INT_MAX
        else:
            return super()._do_validate()


class FloatValue(NumberValue):
    def var_type(self):
        return float


class BoolValue(VariableValue):
    def var_type(self):
        return bool

    def _do_load(self, line, pos=0):
        pos, word = extract_word(line, pos)
        if word == 'true':
            self.value = True
            return
        if word == 'false':
            self.value = False
            return
        raise ParseError(-1, pos,
                         'expected true or false, {} found'.format(word))
        return pos

    def _do_save(self):
        return 'true' if self.value else 'false'


class StrValue(VariableValue):
    def var_type(self):
        return str

    def _do_load(self, line, pos=0):
        pos, self.value = extract_string(line, pos)
        return pos

    def _do_save(self):
        return repr(self.value)


class CharValue(StrValue):
    def _do_validate(self):
        if type(self.value) is str and len(self.value) != 1:
            return False
        return super()._do_validate()

    def _do_load(self, line, pos=0):
        pos = super()._do_load(line, pos)
        if len(self.value) != 1:
            raise ParseError(-1, pos,
                             'excepted one character in char type, {} found'
                             .format(len(self.value)))
        return pos


class ArrayValue(VariableValue):
    def var_type(self):
        return list

    def _do_validate(self):
        if super()._do_validate():
            return True
        for item in self.value:
            item_value.value = item
            if not item_value._do_validate():
                return False
        return True

    def _do_load(self, line, pos=0):
        pos = skip_spaces(line, pos)
        if pos >= len(line) or line[pos] != '[':
            raise ParseError(-1, pos, 'expected \'[\'')
        pos += 1
        self.value = []
        while True:
            pos = skip_spaces(line, pos)
            if pos >= len(line):
                raise ParseError(-1, pos, 'unterminated array')
            if line[pos] == ']':
                return pos + 1
            if len(self.value) != 0:
                if line[pos] != ',':
                    raise ParseError(-1, pos, 'comma expected')
                pos += 1
            pos = self.item_value.load(line, pos)
            self.value += [self.item_value.value]

    def _do_save(self):
        res = '['
        for item in self.value:
            self.item_value.value = item
            res += self.item_value.save() + ', '
        return res[:-2] + ']'

    def __init__(self, item_class, value=None):
        self.item_class = item_class
        self.item_value = item_class()


class TypiniTree:
    def __init_(self):
        pass
