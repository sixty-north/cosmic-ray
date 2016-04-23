import contextlib
import os.path
from pathlib import Path
import sys

import cosmic_ray.modules

THIS_DIR = Path(
    os.path.dirname(
        os.path.realpath(__file__)))


@contextlib.contextmanager
def excursion(directory):
    old_dir = os.getcwd()
    os.chdir(str(directory))
    sys.path = [str(directory)] + sys.path
    try:
        yield
    finally:
        sys.path = sys.path[1:]
        os.chdir(old_dir)


def test_small_directory_tree():
    datadir = THIS_DIR / 'data'
    paths = (('a', '__init__.py'),
             ('a', 'b.py'),
             ('a', 'c', '__init__.py'),
             ('a', 'c', 'd.py'))
    expected = [datadir / Path(*path) for path in paths]
    with excursion(datadir):
        results = sorted(map(
            lambda m: m.__file__,
            cosmic_ray.modules.find_modules('a')))
        assert sorted(map(str, expected)) == results
