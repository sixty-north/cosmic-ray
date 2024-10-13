"""Functions related to finding modules for testing."""

import glob
from pathlib import Path


def find_modules(module_paths):
    """Find all modules in the module (possibly package) represented by ``module_path``.

    Args:
        module_paths: A list of pathlib.Path to Python packages or modules.

    Returns:
        An iterable of paths Python modules (i.e. \\*py files).
    """
    for module_path in module_paths:
        if not module_path.exists():
            raise FileNotFoundError(f"Could not find module path {module_path}")
        if module_path.is_file():
            if module_path.suffix == ".py":
                yield module_path
        elif module_path.is_dir():
            pyfiles = glob.glob(f"{module_path}/**/*.py", recursive=True)
            yield from (Path(pyfile) for pyfile in pyfiles)


def filter_paths(paths, excluded_paths):
    """Filter out path matching one of excluded_paths glob

    Args:
        paths: path to filter.
        excluded_paths: List for glob of modules to exclude.

    Returns:
        An iterable of paths Python modules (i.e. \\*py files).
    """
    excluded = set(Path(f) for excluded_path in excluded_paths for f in glob.glob(excluded_path, recursive=True))
    return set(paths) - excluded
