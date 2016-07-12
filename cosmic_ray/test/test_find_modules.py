from pathlib import Path
import contextlib
import os
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
    old_dir = os.getcwd()
    os.chdir(str(directory))
    try:
        yield
    finally:
        sys.path = sys.path[1:]
        os.chdir(old_dir)


def test_small_directory_tree():
    datadir = THIS_DIR / 'data'
    paths = (('a', '__init__.py'),
             ('a', 'b.py'),
             ('a', 'py.py'),
             ('a', 'c', '__init__.py'),
             ('a', 'c', 'd.py'))
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir):
        results = sorted(
            Path(m.__file__)
            for m in cosmic_ray.modules.find_modules('a'))
    assert expected == results

def test_finding_modules_via_dir_name():
    datadir = THIS_DIR / 'data'
    paths = (('a', 'c', '__init__.py'),
            ('a', 'c', 'd.py'))
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir):
        results = sorted(
            Path(m.__file__)
            for m in cosmic_ray.modules.find_local_modules('a/c'))
    assert expected == results

def test_finding_modules_via_dir_name_and_filename_ending_in_py():
    datadir = THIS_DIR / 'data'
    paths = (('a', 'c', 'd.py'),)
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir):
        results = sorted(
            Path(m.__file__)
            for m in cosmic_ray.modules.find_local_modules('a/c/d.py'))
    assert expected == results

def test_finding_module_py_dot_py_using_dots():
    datadir = THIS_DIR / 'data'
    paths = (('a', 'py.py'),)
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir):
        results = sorted(
            Path(m.__file__)
            for m in cosmic_ray.modules.find_local_modules('a.py'))
    # a.py is not a path so we load a/py.py
    assert expected == results

def test_finding_modules_py_dot_py_using_slashes():
    datadir = THIS_DIR / 'data'
    paths = (('a', 'py.py'),)
    with extend_path(datadir):
        results = sorted(
            Path(m.__file__)
            for m in cosmic_ray.modules.find_local_modules('a/py'))
    # a/py isn't a directory so nothing is loaded
    assert [] == results

def test_finding_modules_py_dot_py_using_slashes_with_full_filename():
    datadir = THIS_DIR / 'data'
    paths = (('a', 'py.py'),)
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir):
        results = sorted(
            Path(m.__file__)
            for m in cosmic_ray.modules.find_local_modules('a/py.py'))
    # a/py.py is a module and it is loaded
    assert expected == results
