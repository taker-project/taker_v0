from .parser import *
from .parseutils import *
import pytest
import math


def test_unescape():
    assert unescape_str('\\033') == '\033'
    assert unescape_str('Строка\\n') == 'Строка\n'
    assert unescape_str('\\\'\\"') == '\'"'


def test_parse_error():
    assert str(ParseError(3, 4, 'test')) == 'error:4:5: test'


def test_extract_string():
    assert extract_string(' \"Hello \\\"hello\\\"!\" ',
                          0) == (19, 'Hello \"hello\"!')
    with pytest.raises(ParseError):
        extract_string(' \"42\'', 0)
    with pytest.raises(ParseError):
        extract_string(' \"42\\\"', 0)


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
    with pytest.raises(ParseError):
        int_value.load('123456789012345678901234567')
    with pytest.raises(ParseError):
        int_value.load('-123456789012345678901234567')


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
    bool_value.load('  true  ')
    assert bool_value.value is True
    assert bool_value.save() == 'true'
    bool_value.load('  false')
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
    char_value.load(' \"4\"  ')
    with pytest.raises(ParseError):
        char_value.load('\'ab\'')
    with pytest.raises(ParseError):
        char_value.load('\'\'')


def test_array():
    int_array = ArrayValue(IntValue)
    int_array.load(' [  1,2,3, 4,   5]')
    assert int_array.value == [1, 2, 3, 4, 5]
    assert int_array.save() == '[1, 2, 3, 4, 5]'
    str_array = ArrayValue(StrValue)
    str_array.load(' [null, "a", \'42\\\'\\\\1\',"3",   "#longlongln"   ] ')
    assert str_array.value == [None, 'a', "42'\\1", '3', '#longlongln']
    assert str_array.save() == "[null, 'a', \"42'\\\\1\", '3', '#longlongln']"
    char_array = ArrayValue(CharValue)
    char_array.value = ['"', "'"]
    assert char_array.save() == '[\'"\', "\'"]'


def test_type_binder():
    binder = TypeBinder()
    assert binder.create_value('int').type_name() == 'int'
    assert binder.create_value('int[]').type_name() == 'int[]'
    with pytest.raises(KeyError):
        binder.create_value('q')
