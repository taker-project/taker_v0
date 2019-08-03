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
        if isinstance(language, str):
            language = self.get_lang(language)
        return SourceCode(self, src_file, exe_file, language, library_dirs)

    def __init__(self, repo_manager):
        super().__init__()
        self.repo_manager = repo_manager
        self.repo = repo_manager.repo
