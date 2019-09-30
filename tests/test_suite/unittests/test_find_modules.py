from pathlib import Path
from cosmic_ray.modules import find_modules, filter_paths


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


def test_small_directory_tree_with_excluding_files(data_dir, path_utils):
    paths = (('a', 'b.py'), ('a', 'py.py'),
             ('a', 'c', 'd.py'))
    excluded_modules = ['**/__init__.py']
    expected = set(Path(*path) for path in paths)

    with path_utils.excursion(data_dir):
        results = find_modules(Path('a'))
        results = filter_paths(results, excluded_modules)
        assert expected == results


def test_small_directory_tree_with_excluding_dir(data_dir, path_utils):
    paths = (('a', '__init__.py'), ('a', 'b.py'), ('a', 'py.py'))
    excluded_modules = ['*/c/*']
    expected = set(Path(*path) for path in paths)

    with path_utils.excursion(data_dir):
        results = find_modules(Path('a'))
        results = filter_paths(results, excluded_modules)
        assert expected == results
