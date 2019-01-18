from enum import Enum, unique
from copy import deepcopy
from .parser import Typini, TypiniSection
from .parseutils import TypiniError


@unique
class MergeOptions(Enum):
    ALLOW_ADD_VAR = 1
    ALLOW_ADD_SECTION = 2
    ALLOW_CHANGE_TYPE = 3


@unique
class MergeCasePolicy(Enum):
    NO_CASE_CHANGE = 0
    AS_DEST = 1
    AS_SOURCE = 2


class MergeError(TypiniError):
    pass


DEFAULT_OPTIONS = {}


def merge_section(dest, source, options=None,
                  policy=MergeCasePolicy.NO_CASE_CHANGE):
    '''Merge source into dest'''
    assert isinstance(dest, TypiniSection)
    assert isinstance(source, TypiniSection)
    if options is None:
        options = DEFAULT_OPTIONS
    for src_node in source:
        src_key = src_node.key
        if not dest.exists(src_key, False):
            if MergeOptions.ALLOW_ADD_VAR not in options:
                raise MergeError('variable {}::{} doesn\'t exist in target'
                                 .format(source.key, src_key))
            key = src_key
        elif not dest.exists(src_key, True):
            if policy == MergeCasePolicy.NO_CASE_CHANGE:
                raise MergeError('variable {}::{} has different cases in '
                                 'source and target'
                                 .format(source.key, src_key))
            elif policy == MergeCasePolicy.AS_DEST:
                dest.rename(dest.find_node(key, False).key, src_key)
                key = src_key
            elif policy == MergeCasePolicy.AS_SOURCE:
                key = src_key
            else:
                assert False, 'we should never enter here'
        else:
            key = src_key
        try:
            dest.reset(src_key, src_node.value.type_name(),
                       src_node.value.value)
        except KeyError:
            raise MergeError('type mismatch for {}::{}'
                             .format(source.key, src_key))


def merge(dest, source, options=None, policy=MergeCasePolicy.NO_CASE_CHANGE):
    '''Merge source into dest'''
    assert isinstance(dest, Typini)
    assert isinstance(source, Typini)
    if options is None:
        options = DEFAULT_OPTIONS
    for src_section in source:
        src_key = src_section.key
        if not dest.has_section(src_key, False):
            if MergeOptions.ALLOW_ADD_SECTION not in options:
                raise MergeError('section {} doesn\'t exist in target'
                                 .format(src_key))
            dst_section = dest.create_section(src_key)
        elif not dest.has_section(src_key, True):
            if policy == MergeCasePolicy.NO_CASE_CHANGE:
                raise MergeError('section {} has different cases in source '
                                 'and target'.format(src_key))
            elif policy == MergeCasePolicy.AS_SOURCE:
                dest.rename(dest.find_section(src_key).key,
                            src_section.key)
            dst_section = dest.find_section(src_key, False)
        else:
            dst_section = dest.find_section(src_key, True)
        merge_section(src_section, dst_section, options, policy)
