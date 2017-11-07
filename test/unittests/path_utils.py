import contextlib
import os
from pathlib import Path
import sys


_THIS_DIR = Path(
    os.path.dirname(
        os.path.realpath(__file__)))

DATA_DIR = _THIS_DIR / 'data'


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


@contextlib.contextmanager
def extend_path(directory):
    """Put `directory` at the front of `sys.path` temporarily.
    """
    sys.path = [str(directory)] + sys.path
    try:
        yield
    finally:
        sys.path = sys.path[1:]
