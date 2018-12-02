import contextlib
import os
from pathlib import Path
import sys


@contextlib.contextmanager
def excursion(directory):
    """Context manager for temporarily setting `directory` as the current working
    directory.
    """
    old_dir = os.getcwd()
    os.chdir(str(directory))
    try:
        yield
    finally:
        os.chdir(old_dir)
