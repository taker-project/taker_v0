import math
import pytest
from typini.parser import *
from typini.parseutils import *


def test_unescape():
    assert unescape_str('\\033') == '\033'
    assert unescape_str('Строка\\n') == 'Строка\n'
    assert unescape_str('\\\'\\"') == '\'"'


def test_parse_error():
    assert str(ParseError(3, 4, 'test')) == '4:5: error: test'


def test_extract_string():
    assert extract_string(' \"Hello \\\"hello\\\"!\" ',
                          0) == (19, 'Hello \"hello\"!')

    with pytest.raises(ParseError) as excinfo:
        extract_string(' \"42\'', 0)
    assert excinfo.value.text == 'string is not terminated'

    with pytest.raises(ParseError) as excinfo:
        extract_string(' \"42\\\"', 0)
    assert excinfo.value.text == 'string is not terminated'


def test_null():
    null_value = IntValue()
    null_value.load(' null  ')
    assert null_value.value is None
    assert null_value.save() == 'null'


def test_int():
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


def test_float():
    float_value = FloatValue()
    float_value.load(' 3.14159 ')
    assert float_value.value == 3.14159
    assert float_value.save() == '3.14159'

    float_value.load('nan')
    assert math.isnan(float_value.value)

    float_value.load('inf')
    assert math.isinf(float_value.value)


def test_bool():
    bool_value = BoolValue()

    assert bool_value.load('  true  ') == 6
    assert bool_value.value is True
    assert bool_value.save() == 'true'

    assert bool_value.load('  false') == 7
    assert bool_value.value is False
    assert bool_value.save() == 'false'


def test_string():
    str_value = StrValue()

    str_value.load(' \"Demo\\\"string\"  ')
    assert str_value.value == 'Demo\"string'
    assert str_value.save() == '\'Demo"string\''

    str_value.load(' \"\"    ')
    assert str_value.value == ''

    str_value.load('"Стр\'ока"')
    assert str_value.value == 'Стр\'ока'
    assert str_value.save() == '"Стр\'ока"'


def test_char():
    char_value = CharValue()

    char_value.load(' "4"  ')
    assert char_value.save() == "c'4'"

    char_value.load('  c"4"  ')
    assert char_value.save() == "c'4'"

    with pytest.raises(ParseError):
        char_value.load('c "4"')

    with pytest.raises(ParseError) as excinfo:
        char_value.load('\'ab\'')
    assert (excinfo.value.text ==
            'one character in char type expected, 2 character(s) found')

    with pytest.raises(ParseError) as excinfo:
        char_value.load('\'\'')
    assert (excinfo.value.text ==
            'one character in char type expected, 0 character(s) found')


def test_array():
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
    assert char_array.save() == '[c\'"\', c"\'"]'

    char_array.value[0] = 42
    assert not char_array.is_valid()
    char_array.value = None
    assert char_array.is_valid()


def test_type_binder():
    binder = TypeBinder()
    assert binder.create_value('int').type_name() == 'int'
    assert binder.create_value('int[]').type_name() == 'int[]'
    with pytest.raises(KeyError):
        binder.create_value('q')


class BinderContainer:
    def __init__(self):
        self.binder = TypeBinder()


def test_nodes():
    binder_container = BinderContainer()

    empty_node = EmptyNode(binder_container)
    empty_node.load('   # komment   ')
    assert empty_node.comment == ' komment   '

    var_node = VariableNode(binder_container)

    with pytest.raises(ValueError):
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


def test_auto():
    binder_container = BinderContainer()
    node = VariableNode(binder_container)

    node.load('a:auto=42')
    assert node.save() == 'a: int = 42'

    node.load('a=33.0')
    assert node.save() == 'a: float = 33.0'

    node.load('a =  0')
    assert node.save() == 'a: int = 0'

    node.load('my-long-identifier : auto = false')
    assert node.save() == 'my-long-identifier: bool = false'

    node.load('  b = "4"')
    assert node.save() == "b: string = '4'"

    node.load("a = c'4'")
    assert node.save() == "a: char = c'4'"

    node.load('b = [1, 2, 3, 4, 5]')
    assert node.save() == 'b: int[] = [1, 2, 3, 4, 5]'

    node.load('a:auto=[1,2.0,0,-3.5,null]')
    assert node.save() == 'a: float[] = [1.0, 2.0, 0.0, -3.5, null]'


def test_auto_errors():
    binder_container = BinderContainer()
    node = VariableNode(binder_container)

    with pytest.raises(ParseError) as excinfo:
        node.load('a: auto')
    assert excinfo.value.text == "'=' expected"

    with pytest.raises(ParseError) as excinfo:
        node.load('a: auto 42')
    assert excinfo.value.text == "'=' expected"

    with pytest.raises(ParseError) as excinfo:
        node.load('   a')
    assert excinfo.value.text == "':' or '=' expected"

    with pytest.raises(ParseError) as excinfo:
        node.load('a, int')
    assert excinfo.value.text == "':' or '=' expected"

    with pytest.raises(ParseError) as excinfo:
        node.load('a = null')
    assert excinfo.value.text == 'found null, cannot auto-deduce type'

    with pytest.raises(ParseError) as excinfo:
        node.load('a = monster')
    assert excinfo.value.text == 'no type candidates found'

    with pytest.raises(ParseError) as excinfo:
        node.load('b = "hello')
    assert (excinfo.value.text ==
            'string is not terminated (assuming deduced type as string)')


def test_section():
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
        section.erase('key')
    section.erase('KEY')

    assert len(section) == 1
    section.reset('KEY', 'string', 'value')
    section.reset('key', 'string', 'value2')
    section.reset('hello', 'int', 42, False)
    section.reset('hello', 'int', 43, False)
    assert len(section) == 3

    with pytest.raises(KeyError):
        section.reset('HELLO', 'string', 'value', False)
    with pytest.raises(KeyError):
        section.reset('HELLO', 'int', 42, False)

    with pytest.raises(ValueError):
        section['key'] = 42
    section['key'] = 'new_key'
    assert section['key'] == 'new_key'

    with pytest.raises(ParseError):
        node = VariableNode(binder_container)
        node.reset('key', 'int', 42)
        section.append_node(node)
    with pytest.raises(ParseError):
        node = VariableNode(binder_container)
        node.reset('Key', 'int', 42)
        section.append_node(node)

    section.clear()

    comm_node = EmptyNode(binder_container)
    comm_node.comment = ' 42'
    section.append_node(comm_node)

    var_node = VariableNode(binder_container)
    var_node.reset('a', 'int', 1)
    var_node.comment = ' Hello'
    section.append_node(var_node)

    assert section.dump() == '[head]\n# 42\na: int = 1 # Hello'
    with pytest.raises(ParseError):
        section.append_node(SectionNode(binder_container, '42'))
    section.reset('A', 'string', '2')
    assert section.dump() == '[head]\n# 42\nA: string = \'2\' # Hello'
    section.reset('b', 'int', 3)
    section.reset('a', 'int', 3)
    section.append_node(EmptyNode(binder_container, ' 42'))
    assert section.dump() == '''[head]
# 42
a: int = 3 # Hello
b: int = 3
# 42'''
    section.reset('c', 'int', 42)
    assert (section.dump() ==
            '[head]\n# 42\na: int = 3 # Hello\nb: int = 3\nc: int = 42\n# 42')

    section.reset('d', 'int', None)
    assert section.get_value('d', 'no val') == 'no val'
    assert section.get_value('e', 'no val') == 'no val'
    assert section.get_value('a', 'no val') == 3


def test_full():
    parser = Typini()
    parser.load(
        '[section]\n  a : int = 5\nb: int = 6 # comment\n#another_comment\n\n'
        '[section2]\n c : string\n d:int=2')
    assert len(parser) == 8
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

    parser.append_lines('[section]\nd:string')
    assert (parser.dump() ==
            '[section2]\nc: string\nd: int = 2\n[section]\nd: string')

    parser.load('#comment\n\n\n\n[section]\na:int\n#\n\n[sect2]\n[sect3]\n')

    parser.clear()
    parser.ensure_section('hello')
    assert parser.dump() == '[hello]'
    with pytest.raises(KeyError):
        parser.ensure_section('HELLO', False)
    parser.ensure_section('HELLO')
    assert parser.dump() == '[HELLO]'
    parser.ensure_section('test')
    assert parser.dump() == '[HELLO]\n[test]'
    parser.ensure_section('Section')
    assert parser.dump() == '[HELLO]\n[test]\n[Section]'
    parser.erase_section('HELLO')
    assert parser.dump() == '[test]\n[Section]'
    parser.create_section('42')
    assert parser.dump() == '[test]\n[Section]\n[42]'
    with pytest.raises(ParseError):
        parser.create_section('TEST')
    with pytest.raises(ParseError):
        parser.create_section('test')

    with pytest.raises(ParseError) as excinfo:
        parser.load('a:int=5\n[section]')
    assert (excinfo.value.text ==
            'only blanks and comments are allowed outside of sections')

    with pytest.raises(ParseError) as excinfo:
        parser.load('[section]\na:q=5\n')
    assert excinfo.value.text == 'unknown type q'

    with pytest.raises(ParseError) as excinfo:
        parser.load('[section]\n--help:int=5\n')
    assert str(excinfo.value) == '2:1: error: invalid variable name: --help'

    with pytest.raises(ParseError) as excinfo:
        parser.load('[--help]')
    assert excinfo.value.text == 'invalid section name: --help'

    with pytest.raises(ParseError) as excinfo:
        parser.load('[section]\na:int\nA:int\n')
    assert (excinfo.value.text ==
            'key A is duplicate or only the case differs')


def test_rename():
    parser = Typini()
    parser.load('[small]\nbigA=1\nSMALLb=2\nBIGC=3\n# comment\n[BIG]\nq=1')
    assert parser.dump() == '''[small]
bigA: int = 1
SMALLb: int = 2
BIGC: int = 3
# comment
[BIG]
q: int = 1'''

    with pytest.raises(TypiniError) as excinfo:
        parser.rename_section('nonExistent', '42')
    assert str(excinfo.value) == 'nonExistent doesn\'t exist'

    with pytest.raises(TypiniError) as excinfo:
        parser.rename_section('BIG', 'INVALID!')
    assert str(excinfo.value) == 'INVALID! is a bad section name'

    with pytest.raises(TypiniError) as excinfo:
        parser.rename_section('BIG', 'SMALL')
    assert str(excinfo.value) == 'SMALL already exists'

    with pytest.raises(TypiniError) as excinfo:
        parser.rename_section('big', 'good')
    assert str(excinfo.value) == 'big doesn\'t exist'

    parser.rename_section('BIG', 'big')
    assert parser.dump() == '''[small]
bigA: int = 1
SMALLb: int = 2
BIGC: int = 3
# comment
[big]
q: int = 1'''

    parser.rename_section('big', 'VeryBig')
    assert parser.dump() == '''[small]
bigA: int = 1
SMALLb: int = 2
BIGC: int = 3
# comment
[VeryBig]
q: int = 1'''

    section = parser['small']

    with pytest.raises(TypiniError) as excinfo:
        section.rename('nonExistent', '42')
    assert str(excinfo.value) == 'nonExistent doesn\'t exist'

    with pytest.raises(TypiniError) as excinfo:
        section.rename('BIGC', 'INVALID!')
    assert str(excinfo.value) == 'INVALID! is a bad key name'

    with pytest.raises(TypiniError) as excinfo:
        section.rename('BIGC', 'BIGA')
    assert str(excinfo.value) == 'BIGA already exists'

    with pytest.raises(TypiniError) as excinfo:
        section.rename('bigc', 'good')
    assert str(excinfo.value) == 'bigc doesn\'t exist'

    section.rename('bigA', 'BIGA')
    assert parser.dump() == '''[small]
BIGA: int = 1
SMALLb: int = 2
BIGC: int = 3
# comment
[VeryBig]
q: int = 1'''

    section.rename('SMALLb', 'smallest_b')
    assert parser.dump() == '''[small]
BIGA: int = 1
smallest_b: int = 2
BIGC: int = 3
# comment
[VeryBig]
q: int = 1'''


def test_iter():
    parser = Typini()
    parser.load('[f]\ne=1\n#\nd=2\n[c]\nb=1\n#\na=2')

    all_sections = [section.key for section in parser]
    all_nodes = [node.key for section in parser for node in section]

    assert all_sections == ['f', 'c']
    assert all_nodes == ['e', 'd', 'b', 'a']
