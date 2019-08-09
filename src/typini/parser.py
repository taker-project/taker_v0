import itertools
from compat import fspath
from .names import is_char_valid, is_var_name_valid
from .parseutils import *

# TODO : fix that array of nulls is of type int[]
# (it's an error or null must be deduced to type int also?)


class EmptyNode:
    @classmethod
    def can_load(cls, line):
        char = next_nonspace(line)
        return char in ('', '#')

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
    def is_valid(self):
        if self.value is None:
            return True
        return type(self.value) == self.var_type()

    def type_name(self):
        raise NotImplementedError()

    def var_type(self):
        raise NotImplementedError()

    def validate(self):
        if not self.is_valid():
            raise ValueError('{} contains an invalid value'
                             .format(type(self).__name__))

    def _do_load(self, line, pos=0):
        raise NotImplementedError()

    def load(self, line, pos=0):
        new_pos, _, word = extract_word(line, pos)
        if word == 'null':
            self.value = None
            return new_pos
        pos = self._do_load(line, pos)
        if not self.is_valid():
            raise ParseError(-1, pos, '{} contains an invalid value'
                             .format(type(self).__name__))
        return pos

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
        pos, start_pos, word = extract_word(line, pos)
        try:
            self.value = self.var_type()(word)
            self.validate()
        except ValueError:
            raise ParseError(-1, start_pos, '{} expected, {} token found'
                             .format(self.var_type().__name__,
                                     repr(word)))
        return pos


class IntValue(NumberValue):
    def var_type(self):
        return int

    def type_name(self):
        return 'int'

    def is_valid(self):
        if isinstance(self.value, int):
            return INT_MIN <= self.value and self.value <= INT_MAX
        return super().is_valid()


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
        pos, start_pos, word = extract_word(line, pos)
        if word == 'true':
            self.value = True
            return pos
        if word == 'false':
            self.value = False
            return pos
        raise ParseError(-1, start_pos, 'expected true or false')

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
    def is_valid(self):
        if isinstance(self.value, str) and len(self.value) != 1:
            return False
        return super().is_valid()

    def type_name(self):
        return 'char'

    def _do_save(self):
        return 'c' + super()._do_save()

    def _do_load(self, line, pos=0):
        pos = skip_spaces(line, pos)
        if (pos != len(line)) and line[pos] == 'c':
            pos += 1
        if (pos == len(line)) or (line[pos] not in {'"', "'"}):
            raise ParseError(-1, pos, '\' or \" expected')
        pos = super()._do_load(line, pos)
        if len(self.value) != 1:
            raise ParseError(-1, pos,
                             'one character in char type expected, '
                             '{} character(s) found'
                             .format(len(self.value)))
        return pos


class ArrayValue(VariableValue):
    def var_type(self):
        return list

    def type_name(self):
        return self.item_value.type_name() + '[]'

    def is_valid(self):
        if self.value is None:
            return True
        if not super().is_valid():
            return False
        for item in self.value:
            self.item_value.value = item
            if not self.item_value.is_valid():
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
            if self.value:
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
        super().__init__(value)
        self.item_class = item_class
        self.item_value = item_class()


class TypeDetector:
    def __init__(self, binder, line, pos=0):
        self.binder = binder
        self.best_exception = None
        self.best_typename = None
        self.line = line
        self.pos = pos
        self.new_pos = pos
        self.value = None
        self.found = False

    def update_exception(self, typename, new_exception):
        if new_exception.column <= skip_spaces(self.line, self.pos):
            return
        if ((self.best_exception is None) or
                (new_exception.column > self.best_exception.column)):
            self.best_exception = new_exception
            self.best_typename = typename

    def try_load_detect_type(self, typename):
        if self.found:
            return True
        self.value = self.binder.create_value(typename)
        try:
            self.new_pos = self.value.load(self.line, self.pos)
        except ParseError as exc:
            self.update_exception(self.value.type_name(), exc)
            return False
        if self.value.value is None:
            raise ParseError(-1, self.new_pos,
                             'found null, cannot auto-deduce type')
        self.found = True
        return True

    def get_result(self):
        if self.found:
            return (self.new_pos, self.value)
        if self.best_exception is None:
            raise ParseError(-1, self.pos, 'no type candidates found')
        self.best_exception.text = '{} (assuming deduced type as {})'.format(
            self.best_exception.text, self.best_typename)
        raise self.best_exception


class TypeBinder:
    def _bind_type(self, type_class):
        type_name = type_class().type_name()
        self.__binding[type_name] = type_class
        self.__added_types += [type_name]

    def create_value(self, typename):
        # TODO: Add multi-dimensional array support (?)
        if len(typename) > 2 and typename[-2:] == '[]':
            return ArrayValue(self.__binding[typename[:-2]])
        return self.__binding[typename]()

    def get_all_types(self):
        for typename in self.__added_types:
            yield typename
        for typename in self.__added_types:
            yield typename + '[]'

    def _bind_types(self):
        self._bind_type(IntValue)
        self._bind_type(FloatValue)
        self._bind_type(BoolValue)
        self._bind_type(StrValue)
        self._bind_type(CharValue)

    def __init__(self):
        self.__binding = {}
        self.__added_types = []
        self._bind_types()


class VariableNode(EmptyNode):
    @classmethod
    def can_load(cls, line):
        return is_char_valid(next_nonspace(line))

    def load(self, line, pos=0):
        pos, start_pos, self.key = extract_word(line, pos)
        if not is_var_name_valid(self.key):
            raise ParseError(-1, start_pos,
                             'invalid variable name: {}'.format(self.key))
        pos = skip_spaces(line, pos)
        if (pos == len(line)) or (line[pos] not in {':', '='}):
            raise ParseError(-1, pos, "':' or '=' expected")
        cur_operator = line[pos]
        pos += 1
        if cur_operator == ':':
            return self.__do_load_typed(line, pos)
        if cur_operator == '=':
            return self.__do_load_auto(line, pos)
        assert False, 'we should never reach this line'

    def __do_load_typed(self, line, pos=0):
        pos, start_pos, type_name = extract_word(line, pos, DELIM_CHARS_TYPE)
        if type_name == 'auto':
            pos = skip_spaces(line, pos)
            pos = line_expect(line, pos, '=')
            return self.__do_load_auto(line, pos)
        try:
            self.value = self.parent.binder.create_value(type_name)
        except KeyError:
            raise ParseError(-1, start_pos,
                             'unknown type {}'.format(type_name))
        pos = skip_spaces(line, pos)
        if pos < len(line) and line[pos] == '=':
            pos += 1
            pos = self.value.load(line, pos)
        return super().load(line, pos)

    def __do_load_auto(self, line, pos=0):
        detector = TypeDetector(self.parent.binder, line, pos)
        for typename in self.parent.binder.get_all_types():
            detector.try_load_detect_type(typename)
            if detector.found:
                break
        pos, self.value = detector.get_result()
        return pos

    def reset(self, key, typename, value):
        self.key = key
        self.value = self.parent.binder.create_value(typename)
        self.value.value = value
        self.value.validate()

    def save(self, line=''):
        line += '{}: {}'.format(self.key, self.value.type_name())
        if self.value.value is not None:
            line += ' = {}'.format(self.value.save())
        return super().save(line)

    def __init__(self, parent, key='', value_node='', comment=None):
        super().__init__(parent, comment)
        self.key = key
        self.value = value_node


class SectionNode(EmptyNode):
    @classmethod
    def can_load(cls, line):
        return next_nonspace(line) == '['

    def load(self, line, pos=0):
        pos = skip_spaces(line, pos)
        pos = line_expect(line, pos, '[')
        pos, start_pos, self.key = extract_word(line, pos)
        if not is_var_name_valid(self.key):
            raise ParseError(-1, start_pos,
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
        try:
            node = None
            for node_type in self.__node_types:
                if node_type.can_load(line):
                    node = node_type(self)
                    break
            if node is None:  # fallback to default node type
                node = self.__node_types[0](self)
            node.load(line)
            self._do_append_node(node)
        except ParseError as parse_error:
            parse_error.row = self.__line_counter
            if parse_error.row < 0:
                parse_error.row = len(self)
            if parse_error.column < 0:
                parse_error.column = len(line) - 1
            raise parse_error

    def append_lines(self, text):
        try:
            self.__line_counter = len(self)
            for line in text.splitlines():
                self.append_line(line)
                self.__line_counter += 1
        finally:
            self.__line_counter = -1

    def load(self, text):
        self.clear()
        self.append_lines(text)

    def dump(self):
        return '\n'.join([node.save() for node in self.get_nodes()])

    def load_from_file(self, file_name):
        self.load(open(fspath(file_name), 'r', encoding='utf8').read())

    def save_to_file(self, file_name):
        open(fspath(file_name), 'w', encoding='utf8').write(self.dump())

    def __init__(self):
        self.binder = TypeBinder()
        self.__node_types = [VariableNode, EmptyNode, SectionNode]
        self.__line_counter = -1
        self.clear()


class TypiniSection:
    def __get_node_index(self, key, case_sensitive=True):
        if key.lower() not in self.__keys:
            return -1
        if not case_sensitive:
            key = key.lower()
        for i in range(len(self.__nodes)):
            node = self.__nodes[i]
            if not isinstance(node, VariableNode):
                continue
            node_key = node.key
            if not case_sensitive:
                node_key = node_key.lower()
            if (type(node) == VariableNode) and node_key == key:
                return i
        return -1

    def __getitem__(self, key):
        return self.find_node(key).value.value

    def __setitem__(self, key, value):
        variable = self.find_node(key).value
        variable.value = value
        variable.validate()

    def __iter__(self):
        for node in self.__nodes:
            if type(node) == VariableNode:
                yield node

    def __contains__(self, item):
        return self.exists(item)

    def get_value(self, key, default=None, case_sensitive=True):
        index = self.__get_node_index(key, case_sensitive)
        if index < 0:
            return default
        value = self.__nodes[index].value.value
        return default if value is None else value

    def get_typed(self, key, typename, allow_null=False, case_sensitive=True):
        node = self.find_node(key, case_sensitive)
        if node.value.type_name() != typename:
            raise TypiniError('{}::{} has invalid type {} ({} expected)'
                              .format(self.key, node.key,
                                      node.value.type_name(), typename))
        value = node.value.value
        if (not allow_null) and (value is None):
            raise TypiniError('{}::{} cannot be null'
                              .format(self.key, node.key))
        return value

    def reset(self, key, typename, value, can_overwrite=True):
        index = self.__get_node_index(key, False)
        cur_node = (self.__nodes[index]
                    if index >= 0
                    else VariableNode(self.parent))
        if (not can_overwrite) and index >= 0:
            if cur_node.key != key or cur_node.value.type_name() != typename:
                raise KeyError(key)
        cur_node.reset(key, typename, value)
        if index < 0:
            self.__append_value_node(cur_node)

    def exists(self, key, case_sensitive=True):
        return self.__get_node_index(key, case_sensitive) >= 0

    def find_node(self, key, case_sensitive=True):
        index = self.__get_node_index(key, case_sensitive)
        if index < 0:
            raise KeyError(key)
        return self.__nodes[index]

    def rename(self, key, new_key):
        if not is_var_name_valid(new_key):
            raise TypiniError('{} is a bad key name'.format(new_key))
        index = self.__get_node_index(key)
        if index < 0:
            raise TypiniError('{} doesn\'t exist'.format(key))
        if ((key.lower() != new_key.lower()) and
                new_key.lower() in self.__keys):
            raise TypiniError('{} already exists'.format(new_key))
        self.__nodes[index].key = new_key
        self.__keys.remove(key.lower())
        self.__keys.add(new_key.lower())

    def clear(self):
        self.__nodes.clear()
        self.__comments_tail.clear()

    def __append_value_node(self, node):
        if node.key.lower() in self.__keys:
            raise ParseError(-1, -1,
                             'key {} is duplicate or only the case differs'
                             .format(node.key))
        self.__keys.add(node.key.lower())
        self.__nodes.append(node)

    def erase(self, key):
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
            self.__append_value_node(node)
        elif type(node) == SectionNode:
            raise ParseError(-1, -1,
                             'section nodes inside sections are not allowed')
        else:
            assert False, 'we should not enter here'

    def get_nodes(self):
        return [self.header] + self.__nodes + self.__comments_tail

    def list_keys(self):
        return [node.key
                for node in self.get_nodes()
                if type(node) == VariableNode]

    def dump(self):
        return '\n'.join([node.save() for node in self.get_nodes()])

    def compact_repr(self):
        '''
        Returns the most compact representation of the section with only
        keys and values. If the sections are equal, it's guaranteed that
        their compact representations are also equal.
        '''
        items = sorted([(node.key, node.value.type_name(), node.value.save())
                        for node in self.get_nodes()
                        if type(node) == VariableNode])
        head = '[' + self.key + ']\n'
        return head + '\n'.join([t[0] + ':' + t[1] + '=' + t[2]
                                 for t in items])

    @property
    def key(self):
        return self.header.key

    @key.setter
    def key(self, value):
        self.header.key = value

    def __len__(self):
        return 1 + len(self.__nodes) + len(self.__comments_tail)

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
            if self.__sections:
                self.__sections[-1].append_node(node)
            elif type(node) != EmptyNode:
                raise ParseError(
                    -1, -1,
                    'only blanks and comments are allowed '
                    'outside of sections')
            else:
                self.__header.append(node)

    def clear(self):
        self.__header.clear()
        self.__sections.clear()
        self.__keys.clear()

    def get_nodes(self):
        return list(itertools.chain(self.__header,
                                    *(section.get_nodes()
                                      for section in self.__sections)))

    def __iter__(self):
        return iter(self.__sections)

    def __contains__(self, item):
        return self.has_section(item)

    def __len__(self):
        # FIXME : calculate length more efficiently?
        return len(self.__header) + sum(len(i) for i in self.__sections)

    def __getitem__(self, key):
        return self.find_section(key)

    def __get_section_index(self, key, case_sensitive=True):
        if key.lower() not in self.__keys:
            return -1
        if not case_sensitive:
            key = key.lower()
        for i in range(len(self.__sections)):
            section_key = self.__sections[i].key
            if not case_sensitive:
                section_key = section_key.lower()
            if section_key == key:
                return i
        return -1

    def __append_section(self, section_node):
        if section_node.key.lower() in self.__keys:
            raise ParseError(-1, -1,
                             'section {} is duplicate or only the case differs'
                             .format(section_node.key))
        self.__keys.add(section_node.key.lower())
        self.__sections.append(TypiniSection(self, section_node))
        return self.__sections[-1]

    def create_section(self, key):
        return self.__append_section(SectionNode(self, key))

    def ensure_section(self, key, can_overwrite=True):
        index = self.__get_section_index(key, False)
        if index < 0:
            index = len(self.__sections)
            self.__append_section(SectionNode(self, key))
        section = self.__sections[index]
        if (not can_overwrite) and section.key != key:
            raise KeyError(key)
        section.key = key
        return section

    def get_sections(self):
        return self.__sections

    def list_sections(self):
        return [section.key for section in self.__sections]

    def compact_repr(self):
        '''
        Returns the most compact representation of the file with only
        keys and values. If the sections are equal, it's guaranteed that
        their compact representations are also equal.
        '''
        sections = sorted([(s.key, s) for s in self.__sections])
        return '\n'.join([s[1].compact_repr() for s in sections])

    def has_section(self, key, case_sensitive=True):
        return self.__get_section_index(key, case_sensitive) >= 0

    def find_section(self, key, case_sensitive=True):
        index = self.__get_section_index(key, case_sensitive)
        if index < 0:
            raise KeyError(key)
        return self.__sections[index]

    def erase_section(self, key):
        index = self.__get_section_index(key)
        if index < 0:
            raise KeyError(key)
        self.__sections.pop(index)
        self.__keys.remove(key.lower())

    def rename_section(self, key, new_key):
        if not is_var_name_valid(new_key):
            raise TypiniError('{} is a bad section name'.format(new_key))
        index = self.__get_section_index(key)
        if index < 0:
            raise TypiniError('{} doesn\'t exist'.format(key))
        if ((key.lower() != new_key.lower()) and
                new_key.lower() in self.__keys):
            raise TypiniError('{} already exists'.format(new_key))
        self.__sections[index].key = new_key
        self.__keys.remove(key.lower())
        self.__keys.add(new_key.lower())

    def __init__(self):
        self.__header = []
        self.__sections = []
        self.__keys = set()
        super().__init__()
