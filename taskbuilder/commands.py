from os import path
from pathlib import Path


class File:
    def __str__(self):
        return str(self.filename)

    def __init__(self, filename):
        self.filename = filename


class InputFile(File):
    pass


class OutputFile(File):
    pass


class NullFile(File):
    def __init__(self):
        self.filename = Path(os.path.devnull)


class Command:
    # TODO : Finish it!
    pass
