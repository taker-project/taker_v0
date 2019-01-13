from taskbuilder.commands import *


def test_files():
    infile = InputFile('q.txt')
    outfile = OutputFile('w.txt')
    assert str(infile) == 'q.txt'
    assert str(outfile) == 'w.txt'
