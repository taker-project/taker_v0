from enum import Enum, unique
from copy import deepcopy
from .parser import Typini, TypiniSection
from .parseutils import TypiniError


class MergeError(TypiniError):
    pass


def merge_section(dest, source):
    '''Merge source into dest'''
    for src_node in source:
        src_key = src_node.key
        src_type = src_node.value.type_name()
        try:
            dst_type = dest.find_node(src_key).value.type_name()
            if src_type != dst_type:
                raise MergeError('type mismatch for {}::{}: expected {}, '
                                 'got {}'.format(source.key, src_key,
                                                 dst_type, src_type))
        except KeyError as err:
            pass
        try:
            dest.reset(src_key, src_type, src_node.value.value, False)
        except KeyError as err:
            raise MergeError('key {}::{} exists, but uses different case'
                             .format(source.key, src_key))


def merge(dest, source):
    '''Merge source into dest'''
    for src_section in source:
        try:
            dst_section = dest.ensure_section(src_section.key, False)
        except KeyError as err:
            raise MergeError('section {} exists, but uses different case'
                             .format(src_section.key))
        merge_section(dst_section, src_section)
