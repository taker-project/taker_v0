from typini import *
from os import path
import json


def dump(parser):
    the_dict = {}
    for section in parser.get_sections():
        section_dict = {}
        for key in section.list_keys():
            section_dict[key] = section[key]
        the_dict[section.header.key] = section_dict
    return the_dict


def test_parse_tree():
    test_dir = path.join('src', 'typini', 'tests')
    parser = Typini()
    parser.load_from_file(path.join(test_dir, 'test1.tini'))
    parsed = dump(parser)
    correct = json.loads(
        open(path.join(test_dir, 'test1.json'), 'r', encoding='utf8').read())
    assert parsed == correct
