import contextlib
import os.path
from pathlib import Path
import sys

import cosmic_ray.modules

THIS_DIR = Path(
    os.path.dirname(
        os.path.realpath(__file__)))


@contextlib.contextmanager
def extend_path(directory):
    """Put `directory` at the front of `sys.path` temporarily.
    """
    sys.path = [str(directory)] + sys.path
    try:
        yield
    finally:
        sys.path = sys.path[1:]


def test_small_directory_tree():
    datadir = THIS_DIR / 'data'
    paths = (('a', '__init__.py'),
             ('a', 'b.py'),
             ('a', 'c', '__init__.py'),
             ('a', 'c', 'd.py'))
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir):
        results = sorted(
            Path(m.__file__)
            for m in cosmic_ray.modules.find_modules('a'))
    assert expected == results
