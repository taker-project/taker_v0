import typini
from typini import Typini, ParseError


class ConfigParser:
    def add_file(self, filename):
        try:
            tmp_typini = Typini()
            tmp_typini.load_from_file(str(filename))
            typini.merge(self.__typini, tmp_typini)
        except ParseError as err:
            err.filename = filename
            raise err

    def dump(self):
        result = {}
        for section in self.__typini:
            result[section.key] = {var.key: var.value.value
                                   for var in section}
        return result

    def __init__(self, default_config=''):
        self.__typini = Typini()
        self.__typini.load(default_config)


class Config:
    def __getitem__(self, key):
        return self.__sections.setdefault(key, {})

    def __iter__(self):
        return iter(self.__sections.items())

    def __init__(self, filenames, user_config, default_config=''):
        parser = ConfigParser(default_config)
        for filename in filenames:
            if filename.is_file():
                parser.add_file(filename)
            elif filename == user_config and default_config:
                config_typini = Typini()
                config_typini.load(default_config)
                config_typini.save_to_file(filename)
        self.__sections = parser.dump()
