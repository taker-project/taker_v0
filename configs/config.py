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
            variables = {}
            for var in section:
                variables[var.key] = var.value
            result[section.key] = variables
        return result

    def __init__(self, default_config=''):
        self.__typini = Typini()
        self.__typini.load(default_config)


class Config:
    def __getitem__(self, key):
        return self.__sections.setdefault(key, {})

    def __init__(self, filenames, user_config, default_config=''):
        parser = ConfigParser(default_config)
        for filename in filenames:
            if filename.is_file():
                parser.add_file(filename)
            elif filename == user_config and default_config:
                with open(str(filename), 'w', encoding='utf8') as file:
                    file.write(default_config)
        self.__sections = parser.dump()
