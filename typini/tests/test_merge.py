from typini.merge import *
from typini.parser import Typini
from copy import deepcopy
import pytest


def test_merge():
    a = Typini()
    a.load('''
[sectionA]
x = 5
[sectionC]
a = 5
x = 6
''')

    b = Typini()
    b.load('''
[sectionC]
x = 7
b = 8
[sectionB]
x = 4
''')

    c = deepcopy(a)
    merge(c, b)
    assert c.dump() == '''
[sectionA]
x: int = 5
[sectionC]
a: int = 5
x: int = 7
b: int = 8
[sectionB]
x: int = 4'''

    bad1 = Typini()
    bad1.load('[sectionC]\nX = 5')
    with pytest.raises(MergeError) as excinfo:
        c = deepcopy(a)
        merge(c, bad1)
    assert (str(excinfo.value) ==
            'key sectionC::X exists, but uses different case')

    bad2 = Typini()
    bad2.load('[SECTIONC]\nq = 5')
    with pytest.raises(MergeError) as excinfo:
        c = deepcopy(a)
        merge(c, bad2)
    assert (str(excinfo.value) ==
            'section SECTIONC exists, but uses different case')

    bad3 = Typini()
    bad3.load('[sectionC]\nx = "hello"')
    with pytest.raises(MergeError) as excinfo:
        c = deepcopy(a)
        merge(c, bad3)
    assert (str(excinfo.value) ==
            'type mismatch for sectionC::x: expected int, got string')
