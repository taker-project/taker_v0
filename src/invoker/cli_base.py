import shutil
from pathlib import Path


INVOKER_CMD_NAME = 'take-invoke'


def invoker_exe():
    return Path(shutil.which(INVOKER_CMD_NAME))
