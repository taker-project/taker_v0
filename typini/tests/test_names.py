from typini.names import is_var_name_valid, is_char_valid


def test_char_valid() -> None:
    assert is_char_valid('a')
    assert is_char_valid('q')
    assert is_char_valid('A')
    assert is_char_valid('Q')
    assert is_char_valid('0')
    assert is_char_valid('9')
    assert is_char_valid('.')
    assert is_char_valid('/')
    assert is_char_valid('_')
    assert is_char_valid('-')


def test_name_valid() -> None:
    assert is_var_name_valid('azAZ09-_./')
    assert not is_var_name_valid('#!/bin/bash')
    assert is_var_name_valid('.....')
    assert not is_var_name_valid('')
    assert not is_var_name_valid('-help')
    assert is_var_name_valid('Hello')
