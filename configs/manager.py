import os
from pathlib import Path
import appdirs
from .config import Config


class ConfigPaths:
    @staticmethod
    def __get_config_file(path, config_name):
        return path / (config_name + '.conf')

    @staticmethod
    def __get_config_dir(path, config_name):
        return path / (config_name + '.conf.d')

    def __get_possible_filenames(self, path, config_name):
        result = [self.__get_config_file(path, config_name)]
        conf_dir = self.__get_config_dir(path, config_name)
        if conf_dir.is_dir():
            result += sorted(filter(lambda x: x.is_file(),
                                    conf_dir.iterdir()))
        return result

    def user_config(self, config_name):
        return self.__get_config_file(self.user_paths[0], config_name)

    def filenames(self, config_name):
        result = []
        for path in self.site_paths + self.user_paths:
            result += self.__get_possible_filenames(path, config_name)
        return result

    def __do_init_user(self, path, config_name):
        self.__get_config_dir(path, config_name).mkdir(parents=True,
                                                       exist_ok=True)

    def init_user(self, config_name):
        for path in self.user_paths:
            self.__do_init_user(path, config_name)

    def __init__(self, program_name='taker-project', program_version='v0'):
        self.site_paths = appdirs.site_config_dir(
            program_name, program_version, multipath=True).split(os.pathsep)
        self.site_paths = list(map(Path, self.site_paths))
        user_path = appdirs.user_config_dir(program_name, program_version,
                                            roaming=True)
        self.user_paths = [Path(user_path)]


class ConfigManager:
    def __getitem__(self, config_name):
        if config_name in self.__configs:
            return self.__configs[config_name]
        paths = self.__paths
        paths.init_user(config_name)
        config = Config(paths.filenames(config_name),
                        paths.user_config(config_name),
                        self.__defaults.get(config_name, ''))
        self.__configs[config_name] = config
        return config

    def add_default(self, config_name, value):
        if config_name in self.__defaults:
            raise KeyError(config_name)
        self.__defaults[config_name] = value

    def __init__(self, paths=None):
        if paths is None:
            paths = ConfigPaths()
        self.__paths = paths
        self.__configs = {}
        self.__defaults = {}
