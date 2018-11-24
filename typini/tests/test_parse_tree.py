from typini import *
from os import path
import json


def dump(parser):
    dict = {}
    for section in parser.get_sections():
        section_dict = {}
        for key in section.list_keys():
            section_dict[key] = section[key]
        dict[section.header.key] = section_dict
    return dict


def test_parse_tree():
    test_dir = path.join('typini', 'tests')
    parser = Typini()
    parser.load_from_file(path.join(test_dir, 'test1.tini'))
    parsed = dump(parser)
    correct = json.loads(open(path.join(test_dir, 'test1.json'), 'r').read())
    assert parsed == correct
