from .languages import LanguageManagerBase
from .sourcecode import SourceCode
from . import compiler


class LanguageManager(LanguageManagerBase):
    def detect_language(self, src_file, library_dirs=None):
        return compiler.detect_language(self.repo,
                                        self.get_ext(src_file.suffix),
                                        src_file, library_dirs)

    def create_source(self, src_file, exe_file=None, language=None,
                      library_dirs=None):
        return SourceCode(self, self.repo, src_file, exe_file,
                          language, library_dirs)

    def __init__(self, repo):
        super().__init__()
        self.repo = repo
