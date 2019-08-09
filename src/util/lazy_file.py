import hashlib
from pathlib import Path


class LazyFile:
    def save(self):
        new_digest = hashlib.sha256(self.text.encode()).digest()
        if self.__digest != new_digest:
            self.filename.open('w', encoding='utf8').write(self.text)

    def load(self):
        self.text = ''
        if self.filename.exists():
            self.text = self.filename.open('r', encoding='utf8').read()
        self.__digest = hashlib.sha256(self.text.encode()).digest()

    def __init__(self, filename):
        self.filename = Path(filename)
        self.text = ''
        self.load()
