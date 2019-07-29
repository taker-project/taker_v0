from .languages import Language, LanguageManagerBase
from .sourcecode import SourceCode
import compiler
from os.path import splitext


class LanguageManager(LanguageManagerBase):
    def detect_language(self, src_file, library_dirs=None):
        ext = self.get_ext(splitext(src_file)[1])
        return compiler.detect_language(self.repo, self.get_ext(ext), src_file,
                                        library_dirs)

    def create_source(self, src_file, exe_file=None, language=None,
                      library_dirs=None):
        return SourceCode(self, self.repo, src_file, exe_file,
                          language, library_dirs)

    def __init__(self, repo):
        super().__init__()
        self.repo = repo
