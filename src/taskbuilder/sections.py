'''NOTE: as usual for taskbuilder submodules, the paths are stored using
pathlib.Path and are stored relative to the repository root, NOT to
the current working directory.
'''
import itertools
import hashlib
from typini import Typini
from compat import fspath
from util import LazyFile
from .repository import TaskRepository
from .commands import InputFile


INTERNAL_DIR = 'sections'


def encode_filename(config_name, section_name):
    total_path = '_' + fspath(config_name) + '@@' + section_name
    return total_path.replace('/', '@').replace('\\', '@')


class SectionManager:
    def sections(self):
        res = []
        for config, sections in self.__configs.items():
            res += list(itertools.product([config], sections))
        res.sort()
        return res

    def targets(self):
        return [encode_filename(conf, sect) for conf, sect in self.sections()]

    def add_section(self, config_file, section_name):
        config_file = self.repo.relpath(config_file)
        self.__configs.setdefault(config_file, set())
        self.__configs[config_file].add(section_name)

    def internal_dir(self, absolute=False):
        return self.repo.internal_dir(absolute) / INTERNAL_DIR

    def target_file(self, config_file, section_name, absolute=False):
        config_file = self.repo.relpath(config_file)
        return self.internal_dir(absolute) / encode_filename(config_file,
                                                             section_name)

    def __update_config(self, config_file):
        config_file = self.repo.relpath(config_file)
        abs_config_file = self.repo.abspath(config_file)
        config = None
        if abs_config_file.is_file():
            config = Typini()
            config.load_from_file(self.repo.abspath(config_file))
        for section in self.__configs[config_file]:
            file_path = self.target_file(config_file, section, True)
            if (config is None) or (section not in config):
                if file_path.exists():
                    file_path.unlink()
                continue
            file = LazyFile(file_path)
            file.text = hashlib.sha256(
                config[section].compact_repr().encode()).hexdigest()
            file.text += '\n'
            file.save()

    def __delete_ununsed(self):
        all_files = set(self.internal_dir(True).iterdir())
        all_targets = self.targets()
        for file in all_files:
            if not file.is_file():
                continue
            if file.name not in all_targets:
                file.unlink()

    def update(self):
        for config in self.__configs:
            self.__update_config(config)
        self.__delete_ununsed()

    def get_depend(self, config_name, section):
        return InputFile(self.target_file(config_name, section))

    def __init__(self, repo: TaskRepository):
        self.__configs = {}
        self.repo = repo
        self.internal_dir(True).mkdir(exist_ok=True)
