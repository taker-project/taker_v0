import os
from pathlib import Path
from compat import fspath
from invoker import LanguageManager, default_exe_ext
from typini import Typini, TypiniSection
from taskbuilder import Makefile, RepositoryManager, TaskBuilderSubsystem
from .utils import is_filename_valid


SOURCE_CFG_FILE = 'list.take'


class SourceItemError(Exception):
    pass


class SourceItem:
    def __try_exe_name(self, suffix):
        self.exe_name = (os.path.splitext(self.src_name)[0] + suffix +
                         self.lang.exe_ext)
        if self.exe_name == self.src_name:
            return True
        return self.source_list.can_use_name(self.exe_name)

    def __choose_exe_name(self):
        if self.__try_exe_name(''):
            return
        num = 1
        while not self.__try_exe_name('_' + str(num)):
            num += 1

    def __get_library_dirs(self):
        return []

    @property
    def src_path(self):
        return self.source_list.path / self.src_name

    @property
    def exe_path(self):
        return self.source_list.path / self.exe_name

    def save(self):
        section = self._section
        section.reset('lang', 'string', self.lang.name)
        section.reset('exe-name', 'string', self.exe_name)

    def validate(self):
        if not is_filename_valid(self.src_name):
            raise SourceItemError('"{}" is an invalid source name'
                                  .format(self.src_name))
        if not is_filename_valid(self.exe_name):
            raise SourceItemError('"{}" is an invalid executable name'
                                  .format(self.exe_name))
        exe_ext = os.path.splitext(self.exe_name)[1]
        if exe_ext != self.lang.exe_ext:
            raise SourceItemError('"{}" has an invalid extension for this '
                                  'language ({} expected)'
                                  .format(self.exe_name, self.lang.exe_ext))

    def add_compile_rule(self):
        sections = self.source_list.repo_manager.sections
        section_info = (self.source_list.config_path, self.src_name)
        sections.add_section(*section_info)
        rule = self.code.add_compile_rule()
        if rule is not None:
            rule.add_depend(sections.get_depend(*section_info))
        return rule

    def __init__(self, source_list, section: TypiniSection, lang=None):
        self.source_list = source_list
        self.lang_manager = self.source_list.lang_manager
        self._section = section
        self.src_name = section.key

        if lang is not None:
            self.lang = self.lang_manager.get_lang(lang)
        elif 'lang' in section:
            lang_str = section.get_typed('lang', 'string')
            self.lang = self.lang_manager[lang_str]
        else:
            self.lang = self.lang_manager.detect_language(
                self.src_path, self.__get_library_dirs())

        if 'exe-name' in section:
            self.exe_name = section.get_typed('exe-name', 'string')
        else:
            self.__choose_exe_name()
            assert self.exe_name is not None

        self.validate()
        self.code = source_list.lang_manager.create_source(
            self.src_path, self.exe_path, self.lang, self.__get_library_dirs())


class SourceList:
    @property
    def path(self):
        return self.repo_manager.repo.abspath(self.__subdir)

    def _is_system_section(self, section_name):
        return section_name[0] == '.'

    def __contains__(self, key):
        return key in self.__items

    def __getitem__(self, key):
        return self.__items[key]

    def __len__(self):
        return len(self.__items)

    def __add_source(self, src_name, *args, **kwargs):
        assert is_filename_valid(src_name)
        section_created = False
        if src_name not in self.config:
            self.config.create_section(src_name)
            section_created = True
        try:
            item = SourceItem(self, self.config[src_name], *args, **kwargs)
        except Exception as exc:
            if section_created:
                self.config.erase_section(src_name)
            raise exc
        self._src_files.add(item.src_name)
        self._exe_files.add(item.exe_name)
        self.__items[src_name] = item
        return item

    def can_use_name(self, name):
        return ((name not in self._src_files) and
                (name not in self._exe_files) and
                (name not in self._sys_files))

    def add(self, src_name, lang=None, *args, **kwargs):
        if src_name in self.__items:
            raise SourceItemError('"{}" already exists as a source'
                                  .format(src_name))
        if not is_filename_valid(src_name):
            raise SourceItemError('"{}" is an invalid source name'
                                  .format(src_name))
        if not self.can_use_name(src_name):
            raise SourceItemError('"{}" cannot be used as a source name'
                                  .format(src_name))
        return self.__add_source(src_name, *args, **kwargs)

    def __is_add_candidate(self, cand):
        if not self.can_use_name(cand.name):
            return False
        if not self.lang_manager.get_ext(cand.suffix):
            return False
        return True

    def list_add_candidates(self):
        paths = sorted(list(filter(lambda p: self.__is_add_candidate(p),
                                   self.path.iterdir())))
        return list(map(lambda p: p.name, paths))

    def __rescan_add_error(self):
        added = []
        try:
            for file_name in self.list_add_candidates():
                added.append(self.add(file_name))
        except Exception as exc:
            for item in added:
                self.remove(item.src_name)
            raise exc

    def __rescan_add_noerror(self):
        exceptions = []
        for file_name in self.list_add_candidates():
            try:
                self.add(file_name)
            except Exception as exc:
                exceptions += [exc]
        return exceptions

    def rescan_remove(self):
        keys = list(self.__items.keys())
        for src_name in keys:
            if not (self.path / src_name).exists():
                self.remove(src_name)

    def rescan_add(self, ignore_errors=False):
        '''
        If ignore_errors is set to True, the function returns the list of
        raised exceptions.
        '''
        return (self.__rescan_add_noerror() if ignore_errors
                else self.__rescan_add_error())

    def remove(self, src_name):
        if src_name not in self.__items:
            raise KeyError(src_name)
        item = self.__items[src_name]
        self._src_files.remove(item.src_name)
        self._exe_files.remove(item.exe_name)
        self.__items.pop(item.src_name)
        self.config.erase_section(src_name)

    def load(self):
        for section_name in self.config.list_sections():
            if self._is_system_section(section_name):
                continue
            self.__add_source(section_name)

    def save(self):
        self.validate()
        for key in self.__items:
            self.__items[key].save()
        self.config.save_to_file(self.config_path)

    def add_compile_rules(self):
        makefile = self.repo_manager.makefile
        all_src_rule = makefile.add_phony_rule(
            fspath(self.__subdir),
            description='Builds all the {}.'.format(self.description))
        for key in self.__items:
            rule = self.__items[key].add_compile_rule()
            if rule is not None:
                all_src_rule.add_depend(rule)
        makefile.all_rule.add_depend(all_src_rule)

    def update(self):
        self.save()
        self.add_compile_rules()

    def validate(self):
        for key in self.__items:
            self.__items[key].validate()

    def __init__(self, subdir, repo_manager: RepositoryManager,
                 lang_manager: LanguageManager, description='some sources'):
        self.description = description
        self.repo_manager = repo_manager
        self.lang_manager = lang_manager
        self._src_files = set()
        self._exe_files = set()
        self._sys_files = set()
        self.__items = {}
        self.__subdir = Path(subdir)
        self.config = Typini()
        self.config_path = self.path / SOURCE_CFG_FILE
        if self.config_path.exists():
            self.config.load_from_file(self.config_path)
        self._sys_files.add(SOURCE_CFG_FILE)
        self.load()
        self.repo_manager.add_subsystem(SourceListSubsystem, self)


class SourceListSubsystem(TaskBuilderSubsystem):
    def update(self):
        self.srclist.update()

    def __init__(self, manager, srclist):
        super().__init__(manager)
        self.srclist = srclist
