import typing
import pytest
import math
from typini.parser import *  # type: ignore
from typini.parseutils import *  # type: ignore


def test_unescape() -> None:
    assert unescape_str('\\033') == '\033'
    assert unescape_str('Строка\\n') == 'Строка\n'
    assert unescape_str('\\\'\\"') == '\'"'


def test_parse_error() -> None:
    assert str(ParseError(3, 4, 'test')) == '4:5: error: test'


def test_extract_string() -> None:
    assert extract_string(' \"Hello \\\"hello\\\"!\" ',
                          0) == (19, 'Hello \"hello\"!')

    with pytest.raises(ParseError) as excinfo:
        extract_string(' \"42\'', 0)
    assert excinfo.value.text == 'string is not terminated'

    with pytest.raises(ParseError) as excinfo:
        extract_string(' \"42\\\"', 0)
    assert excinfo.value.text == 'string is not terminated'


def test_null() -> None:
    null_value = IntValue()
    null_value.load(' null  ')
    assert null_value.value is None
    assert null_value.save() == 'null'


def test_int() -> None:
    int_value = IntValue()
    int_value.load('   42   ')
    assert int_value.value == 42
    assert int_value.save() == '42'

    with pytest.raises(ParseError) as excinfo:
        int_value.load('123456789012345678901234567')
    assert (excinfo.value.text ==
            'int expected, \'123456789012345678901234567\' token found')

    with pytest.raises(ParseError) as excinfo:
        int_value.load('-123456789012345678901234567')
    assert (excinfo.value.text ==
            'int expected, \'-123456789012345678901234567\' token found')


def test_float() -> None:
    float_value = FloatValue()
    float_value.load(' 3.14159 ')
    assert float_value.value == 3.14159
    assert float_value.save() == '3.14159'

    float_value.load('nan')
    assert math.isnan(float_value.value)

    float_value.load('inf')
    assert math.isinf(float_value.value)


def test_bool() -> None:
    bool_value = BoolValue()

    assert bool_value.load('  true  ') == 6
    assert bool_value.value is True
    assert bool_value.save() == 'true'

    assert bool_value.load('  false') == 7
    assert bool_value.value is False
    assert bool_value.save() == 'false'


def test_string() -> None:
    str_value = StrValue()

    str_value.load(' \"Demo\\\"string\"  ')
    assert str_value.value == 'Demo\"string'
    assert str_value.save() == '\'Demo"string\''

    str_value.load(' \"\"    ')
    assert str_value.value == ''

    str_value.load('"Стр\'ока"')
    assert str_value.value == 'Стр\'ока'
    assert str_value.save() == '"Стр\'ока"'


def test_char() -> None:
    char_value = CharValue()

    char_value.load(' \"4\"  ')
    assert char_value.save() == '\'4\''

    with pytest.raises(ParseError) as excinfo:
        char_value.load('\'ab\'')
    assert (excinfo.value.text ==
            'one character in char type excepted, 2 character(s) found')

    with pytest.raises(ParseError) as excinfo:
        char_value.load('\'\'')
    assert (excinfo.value.text ==
            'one character in char type excepted, 0 character(s) found')


def test_array() -> None:
    int_array = ArrayValue(IntValue)

    int_array.load(' [  1,2,3, 4,   5]')
    assert int_array.value == [1, 2, 3, 4, 5]
    assert int_array.save() == '[1, 2, 3, 4, 5]'

    with pytest.raises(ParseError) as excinfo:
        int_array.load('42')
    assert excinfo.value.text == '\'[\' expected'

    with pytest.raises(ParseError) as excinfo:
        int_array.load('[1,2,      ')
    assert excinfo.value.text == 'int expected, \'\' token found'

    with pytest.raises(ParseError) as excinfo:
        int_array.load('[1,2      ')
    assert excinfo.value.text == 'unterminated array'

    str_array = ArrayValue(StrValue)
    str_array.load(' [null, "a", \'42\\\'\\\\1\',"3",   "#longlongln"   ] ')
    assert str_array.value == [None, 'a', "42'\\1", '3', '#longlongln']
    assert str_array.save() == "[null, 'a', \"42'\\\\1\", '3', '#longlongln']"

    char_array = ArrayValue(CharValue)
    char_array.value = ['"', "'"]
    assert char_array.save() == '[\'"\', "\'"]'


def test_type_binder() -> None:
    binder = TypeBinder()
    assert binder.create_value('int').type_name() == 'int'
    assert binder.create_value('int[]').type_name() == 'int[]'
    with pytest.raises(KeyError):
        binder.create_value('q')


class BinderContainer:
    def __init__(self):  # type: ignore
        self.binder = TypeBinder()


def test_nodes() -> None:
    binder_container = BinderContainer()

    empty_node = EmptyNode(binder_container)
    empty_node.load('   # komment   ')
    assert empty_node.comment == ' komment   '

    var_node = VariableNode(binder_container)

    with pytest.raises(TypeError):
        var_node.reset('a', 'int', 'gnu')
    with pytest.raises(KeyError):
        var_node.reset('int', 'a', 'gnu')

    var_node.load('a.:int[]=[1,2,3]')
    assert var_node.key == 'a.'
    assert var_node.value.value == [1, 2, 3]
    assert var_node.save() == 'a.: int[] = [1, 2, 3]'

    var_node.load('a: int = null')
    assert var_node.value.value is None
    assert var_node.save() == 'a: int'

    var_node.load('a   :int')
    assert var_node.save() == 'a: int'

    section_node = SectionNode(binder_container)
    section_node.load(' [  42  ]  ')
    assert section_node.key == '42'


def test_section() -> None:
    binder_container = BinderContainer()
    section = TypiniSection(
        binder_container, SectionNode(binder_container, 'head'))

    section.reset('KEY', 'string', 'value')
    assert section['KEY'] == 'value'
    with pytest.raises(KeyError):
        section['key']
    with pytest.raises(KeyError):
        section['key'] = '42'
    with pytest.raises(KeyError):
        section.erase_node('key')
    section.erase_node('KEY')

    assert len(section) == 1
    section.reset('KEY', 'string', 'value')
    section.reset('key', 'string', 'value2')
    assert len(section) == 2

    with pytest.raises(TypeError):
        section['key'] = 42
    section['key'] = 'new_key'
    assert section['key'] == 'new_key'

    with pytest.raises(ParseError):
        node = VariableNode(binder_container)
        node.reset('key', 'int', 42)
        section.append_value_node(node)
    with pytest.raises(ParseError):
        node = VariableNode(binder_container)
        node.reset('Key', 'int', 42)
        section.append_value_node(node)

    section.clear()
    var_node = VariableNode(binder_container)
    var_node.reset('a', 'int', 1)
    var_node.comment = ' Hello'
    section.append_node(var_node)
    assert section.dump() == '[head]\na: int = 1 # Hello'
    with pytest.raises(ParseError):
        section.append_node(SectionNode(binder_container, '42'))
    section.reset('A', 'string', '2')
    assert section.dump() == '[head]\nA: string = \'2\' # Hello'
    section.reset('b', 'int', 3)
    section.reset('a', 'int', 3)
    section.append_node(EmptyNode(binder_container, ' 42'))
    assert section.dump() == '[head]\na: int = 3 # Hello\nb: int = 3\n# 42'
    section.reset('c', 'int', 42)
    assert (section.dump() ==
            '[head]\na: int = 3 # Hello\nb: int = 3\nc: int = 42\n# 42')


def test_full() -> None:
    parser = Typini()
    parser.load(
        '[section]\n  a : int = 5\nb: int = 6 # comment\n#another_comment\n\n'
        '[section2]\n c : string\n d:int=2')
    assert(len(parser) == 8)
    assert parser.list_sections() == ['section', 'section2']
    assert parser['section'].list_keys() == ['a', 'b']
    assert parser['section2'].list_keys() == ['c', 'd']
    assert (parser.dump() == '[section]\na: int = 5\nb: int = 6 # comment\n'
            '#another_comment\n\n[section2]\nc: string\nd: int = 2')
    with pytest.raises(KeyError):
        parser['Section']
    with pytest.raises(KeyError):
        parser['nonExistent']
    with pytest.raises(KeyError):
        parser.erase_section('Section')
    parser.erase_section('section')
    assert parser.dump() == '[section2]\nc: string\nd: int = 2'
    parser.load('#comment\n\n\n\n[section]\na:int\n[section2]\n[section3]\n')

    with pytest.raises(ParseError) as excinfo:
        parser.load('a:int=5\n[section]')
    assert (excinfo.value.text ==
            'only blanks and comments are allowed outside of sections')

    with pytest.raises(ParseError) as excinfo:
        parser.load('[section]\na:q=5\n')
    assert excinfo.value.text == 'unknown type q'

    with pytest.raises(ParseError) as excinfo:
        parser.load('[section]\n--help:int=5\n')
    assert excinfo.value.text == 'invalid variable name: --help'

    with pytest.raises(ParseError) as excinfo:
        parser.load('[--help]')
    assert excinfo.value.text == 'invalid section name: --help'

    with pytest.raises(ParseError) as excinfo:
        parser.load('[section]\na:int\nA:int\n')
    assert (excinfo.value.text ==
            'key section::A is duplicate or only the case differs')
