from .names import *
from .parseutils import *
import itertools


class EmptyNode:
    @classmethod
    def can_load(cls, line):
        c = next_nonspace(line)
        return c == '' or c == '#'

    def load(self, line, pos=0):
        pos = skip_spaces(line, pos)
        if pos == len(line):
            self.comment = None
            return pos
        if line[pos] != '#':
            raise ParseError(-1, pos, 'comment expected')
        self.comment = line[pos+1:]
        return len(line)

    def save(self, line=''):
        if self.comment is None:
            return line
        if line != '':
            line += ' '
        line += '#' + self.comment
        return line

    def __init__(self, parent, comment=None):
        self.parent = parent
        self.comment = comment


class VariableValue:
    def _do_validate(self):
        if self.value is None:
            return True
        return type(self.value) == self.var_type()

    def type_name(self):
        raise NotImplementedError()

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
        except (TypeError, ValueError):
            raise ParseError(-1, pos, '{} expected, {} token found'
                             .format(self.var_type().__name__,
                                     repr(word)))
        return pos


class IntValue(NumberValue):
    def var_type(self):
        return int

    def type_name(self):
        return 'int'

    def _do_validate(self):
        if type(self.value) is int:
            return INT_MIN <= self.value and self.value <= INT_MAX
        else:
            return super()._do_validate()


class FloatValue(NumberValue):
    def var_type(self):
        return float

    def type_name(self):
        return 'float'


class BoolValue(VariableValue):
    def var_type(self):
        return bool

    def type_name(self):
        return 'bool'

    def _do_load(self, line, pos=0):
        pos, word = extract_word(line, pos)
        if word == 'true':
            self.value = True
            return pos
        if word == 'false':
            self.value = False
            return pos
        raise ParseError(-1, pos, 'expected true or false')
        return pos

    def _do_save(self):
        return 'true' if self.value else 'false'


class StrValue(VariableValue):
    def var_type(self):
        return str

    def type_name(self):
        return 'string'

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

    def type_name(self):
        return 'char'

    def _do_load(self, line, pos=0):
        pos = super()._do_load(line, pos)
        if len(self.value) != 1:
            raise ParseError(-1, pos,
                             'one character in char type excepted, '
                             '{} character(s) found'
                             .format(len(self.value)))
        return pos


class ArrayValue(VariableValue):
    def var_type(self):
        return list

    def type_name(self):
        return self.item_value.type_name() + '[]'

    def _do_validate(self):
        if super()._do_validate():
            return True
        for item in self.value:
            self.item_value.value = item
            if not self.item_value._do_validate():
                return False
        return True

    def _do_load(self, line, pos=0):
        pos = skip_spaces(line, pos)
        pos = line_expect(line, pos, '[')
        self.value = []
        while True:
            pos = skip_spaces(line, pos)
            if pos >= len(line):
                raise ParseError(-1, pos, 'unterminated array')
            if line[pos] == ']':
                return pos + 1
            if len(self.value) != 0:
                pos = line_expect(line, pos, ',')
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


class TypeBinder:
    def _bind_type(self, type_class):
        type_name = type_class().type_name()
        self.__binding[type_name] = type_class

    def create_value(self, type):
        # TODO: Add multi-dimensional array support (?)
        if len(type) > 2 and type[-2:] == '[]':
            return ArrayValue(self.__binding[type[:-2]])
        else:
            return self.__binding[type]()

    def __init__(self):
        self.__binding = {}
        self._bind_type(IntValue)
        self._bind_type(FloatValue)
        self._bind_type(CharValue)
        self._bind_type(BoolValue)
        self._bind_type(StrValue)


class VariableNode(EmptyNode):
    @classmethod
    def can_load(cls, line):
        return is_char_valid(next_nonspace(line))

    def load(self, line, pos=0):
        pos, self.key = extract_word(line, pos)
        if not is_var_name_valid(self.key):
            raise ParseError(-1, pos,
                             'invalid variable name: {}'.format(self.key))
        pos = skip_spaces(line, pos)
        pos = line_expect(line, pos, ':')
        pos, type_name = extract_word(line, pos, DELIM_CHARS_TYPE)
        try:
            self.value = self.parent.binder.create_value(type_name)
        except KeyError:
            raise ParseError(-1, pos, 'unknown type {}'.format(type_name))
        pos = skip_spaces(line, pos)
        if pos < len(line) and line[pos] == '=':
            pos += 1
            pos = self.value.load(line, pos)
        return super().load(line, pos)

    def reset(self, key, type, value):
        self.key = key
        self.value = self.parent.binder.create_value(type)
        self.value.value = value
        self.value.validate()

    def save(self, line=''):
        line += '{}: {}'.format(self.key, self.value.type_name())
        if self.value.value is not None:
            line += ' = {}'.format(self.value.save())
        return super().save(line)

    def __init__(self, parent, key='', value='', comment=None):
        super().__init__(parent, comment)
        self.key = key
        self.value = value


class SectionNode(EmptyNode):
    @classmethod
    def can_load(cls, line):
        return next_nonspace(line) == '['

    def load(self, line, pos=0):
        pos = skip_spaces(line, pos)
        pos = line_expect(line, pos, '[')
        pos = skip_spaces(line, pos)
        pos, self.key = extract_word(line, pos)
        if not is_var_name_valid(self.key):
            raise ParseError(-1, pos,
                             'invalid section name: {}'.format(self.key))
        pos = skip_spaces(line, pos)
        pos = line_expect(line, pos, ']')
        return super().load(line, pos)

    def save(self, line=''):
        line += '[{}]'.format(self.key)
        return super().save(line)

    def __init__(self, parent, key='', comment=None):
        super().__init__(parent, comment)
        self.key = key


class NodeList:
    def _do_append_node(self, node):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def get_nodes(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()

    def append_line(self, line):
        line_number = len(self)
        try:
            node = None
            for node_type in self.__node_types:
                if node_type.can_load(line):
                    node = node_type(self)
                    break
            if node is None:
                node = self.__node_types[0](self)
            node.load(line)
            self._do_append_node(node)
        except ParseError as parse_error:
            parse_error.row = line_number
            if parse_error.column < 0:
                parse_error.column = len(line) - 1
            raise parse_error

    def load(self, text):
        self.clear()
        for line in text.splitlines():
            self.append_line(line)

    def dump(self):
        return '\n'.join(map((lambda x: x.save()), self.get_nodes()))

    def load_from_file(self, file_name):
        self.load(open(file_name, 'r').read())

    def save_to_file(self, file_name):
        open(file_name, 'w').write(self.dump())

    def __init__(self):
        self.binder = TypeBinder()
        self.__node_types = [VariableNode, EmptyNode, SectionNode]
        self.clear()


class TypiniSection:
    def __get_node_index(self, key, case_sensitive=True):
        if key.lower() not in self.__keys:
            return -1
        if not case_sensitive:
            key = key.lower()
        for i in range(len(self.__nodes)):
            node = self.__nodes[i]
            node_key = node.key
            if not case_sensitive:
                node_key = node_key.lower()
            if (type(node) == VariableNode) and node_key == key:
                return i
        return -1

    def __getitem__(self, key):
        index = self.__get_node_index(key)
        if index < 0:
            raise KeyError(key)
        return self.__nodes[index].value.value

    def __setitem__(self, key, value):
        index = self.__get_node_index(key)
        if index < 0:
            raise KeyError(key)
        self.__nodes[index].value.value = value
        self.__nodes[index].value.validate()

    def reset(self, key, type, value):
        index = self.__get_node_index(key, False)
        cur_node = self.__nodes[
            index] if index >= 0 else VariableNode(self.parent)
        cur_node.reset(key, type, value)
        if index < 0:
            self.append_value_node(cur_node)

    def clear(self):
        self.__nodes.clear()
        self.__comments_tail.clear()

    def append_value_node(self, node):
        if node.key.lower() in self.__keys:
            raise ParseError(-1, -1,
                             'key {}::{} is duplicate or only the case differs'
                             .format(self.header.key, node.key))
        self.__keys.add(node.key.lower())
        self.__nodes.append(node)

    def erase_node(self, key):
        index = self.__get_node_index(key)
        if index < 0:
            raise KeyError(key)
        self.__nodes.pop(index)
        self.__keys.remove(key.lower())

    def append_node(self, node):
        if type(node) == EmptyNode:
            self.__comments_tail.append(node)
        elif type(node) == VariableNode:
            self.__nodes.extend(self.__comments_tail)
            self.__comments_tail.clear()
            self.append_value_node(node)
        elif type(node) == SectionNode:
            raise ParseError(-1, -1,
                             'section nodes inside sections are not allowed')
        else:
            assert False

    def get_nodes(self):
        return [self.header] + self.__nodes + self.__comments_tail

    def list_keys(self):
        return [node.key
                for node in self.get_nodes()
                if type(node) == VariableNode]

    def dump(self):
        return '\n'.join(map((lambda x: x.save()), self.get_nodes()))

    def __len__(self):
        return len(self.__nodes) + len(self.__comments_tail) + 1

    def __init__(self, parent, header):
        self.header = header
        self.__keys = set()
        self.__nodes = []
        self.parent = parent
        self.__comments_tail = []


class Typini(NodeList):
    def _do_append_node(self, node):
        if type(node) == SectionNode:
            self.__append_section(node)
        else:
            if len(self.__sections) > 0:
                self.__sections[-1].append_node(node)
            else:
                if type(node) != EmptyNode:
                    raise ParseError(
                        -1, -1,
                        'only blanks and comments are allowed '
                        'outside of sections')
                self.__header.append(node)

    def clear(self):
        self.__header.clear()
        self.__sections.clear()
        self.__keys.clear()

    def get_nodes(self):
        return list(itertools.chain(self.__header,
                                    *(section.get_nodes()
                                      for section in self.__sections)))

    def __len__(self):
        return len(self.__header) + sum(len(i) for i in self.__sections)

    def __getitem__(self, key):
        index = self.__get_section_index(key)
        if index < 0:
            raise KeyError(key)
        return self.__sections[index]

    def __get_section_index(self, key):
        if key not in self.__keys:
            return -1
        for i in range(len(self.__sections)):
            if self.__sections[i].header.key == key:
                return i
        return -1

    def __append_section(self, section_node):
        if section_node.key in self.__keys:
            raise ParseError(-1, -1,
                             'section {} is duplicate or only the case differs'
                             .format(section_node.key))
        self.__keys.add(section_node.key.lower())
        self.__sections.append(TypiniSection(self, section_node))

    def create_section(self, key):
        self.__append_section(SectionNode(self, key))

    def get_sections(self):
        return self.__sections

    def list_sections(self):
        return [section.header.key for section in self.__sections]

    def erase_section(self, key):
        index = self.__get_section_index(key)
        if index < 0:
            raise KeyError(key)
        self.__sections.pop(index)

    def __init__(self):
        self.__header = []
        self.__sections = []
        self.__keys = set()
        super().__init__()
