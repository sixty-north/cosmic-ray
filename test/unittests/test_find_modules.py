from pathlib import Path

from cosmic_ray.modules import find_modules, fixup_module_name
from path_utils import DATA_DIR, excursion, extend_path


def test_small_directory_tree():
    datadir = DATA_DIR
    paths = (('a', '__init__.py'),
             ('a', 'b.py'),
             ('a', 'py.py'),
             ('a', 'c', '__init__.py'),
             ('a', 'c', 'd.py'))
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir):
        results = sorted(
            Path(m.__file__)
            for m in find_modules('a'))
    assert expected == results


def test_finding_modules_via_dir_name():
    datadir = DATA_DIR
    paths = (('a', 'c', '__init__.py'),
             ('a', 'c', 'd.py'))
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir), excursion(datadir):
        module_name = fixup_module_name('a/c')
        results = sorted(
            Path(m.__file__)
            for m in find_modules(module_name))
    assert expected == results


def test_finding_modules_via_dir_name_and_filename_ending_in_py():
    datadir = DATA_DIR
    paths = (('a', 'c', 'd.py'),)
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir), excursion(datadir):
        module_name = fixup_module_name('a/c/d.py')
        results = sorted(
            Path(m.__file__)
            for m in find_modules(module_name))
    assert expected == results


def test_finding_module_py_dot_py_using_dots():
    datadir = DATA_DIR
    paths = (('a', 'py.py'),)
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir), excursion(datadir):
        module_name = fixup_module_name('a.py')
        results = sorted(
            Path(m.__file__)
            for m in find_modules(module_name))
    # a.py is not a path so we load a/py.py
    assert expected == results


def test_finding_modules_py_dot_py_using_slashes():
    datadir = DATA_DIR
    with extend_path(datadir):
        results = sorted(
            Path(m.__file__)
            for m in find_modules('a/py'))
    # a/py isn't a directory so nothing is loaded
    assert [] == results


def test_finding_modules_py_dot_py_using_slashes_with_full_filename():
    datadir = DATA_DIR
    paths = (('a', 'py.py'),)
    expected = sorted(datadir / Path(*path) for path in paths)
    with extend_path(datadir), excursion(datadir):
        module_name = fixup_module_name('a/py.py')
        results = sorted(
            Path(m.__file__)
            for m
            in find_modules(module_name))
    # a/py.py is a module and it is loaded
    assert expected == results
