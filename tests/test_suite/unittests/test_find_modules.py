from pathlib import Path

from cosmic_ray.modules import find_modules


def test_small_directory_tree(data_dir):
    paths = (('a', '__init__.py'), ('a', 'b.py'), ('a', 'py.py'),
             ('a', 'c', '__init__.py'), ('a', 'c', 'd.py'))
    expected = sorted(data_dir / Path(*path) for path in paths)
    results = sorted(find_modules(data_dir / 'a'))
    assert expected == results


def test_finding_modules_via_dir_name(data_dir):
    paths = (('a', 'c', '__init__.py'), ('a', 'c', 'd.py'))
    expected = sorted(data_dir / Path(*path) for path in paths)
    results = sorted(find_modules(data_dir / 'a' / 'c'))
    assert expected == results


def test_finding_modules_via_dir_name_and_filename_ending_in_py(data_dir):
    paths = (('a', 'c', 'd.py'), )
    expected = sorted(data_dir / Path(*path) for path in paths)
    results = sorted(find_modules(data_dir / 'a' / 'c' / 'd.py'))
    assert expected == results


def test_finding_module_py_dot_py_using_dots(data_dir):
    paths = (('a', 'py.py'), )
    expected = sorted(data_dir / Path(*path) for path in paths)
    results = sorted(find_modules(data_dir / 'a' / 'py.py'))
    assert expected == results


def test_finding_modules_py_dot_py_using_slashes(data_dir):
    results = sorted(find_modules(data_dir / 'a' / 'py'))
    assert [] == results


def test_finding_modules_py_dot_py_using_slashes_with_full_filename(data_dir):
    paths = (('a', 'py.py'), )
    expected = sorted(data_dir / Path(*path) for path in paths)
    results = sorted(find_modules(data_dir / 'a' / 'py.py'))
    assert expected == results
