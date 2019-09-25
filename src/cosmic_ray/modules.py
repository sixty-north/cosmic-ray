"""Functions related to finding modules for testing."""

import glob
from pathlib import Path


def find_modules(module_path, excluded_modules):
    """Find all modules in the module (possibly package) represented by `module_path`.

    Args:
        module_path: A pathlib.Path to a Python package or module.
        excluded_modules: List for glob of modules to exclude.

    Returns: An iterable of paths Python modules (i.e. *py files).
    """
    if module_path.is_dir():
        pyfiles = set(glob.glob('{}/**/*.py'.format(module_path), recursive=True))

    else:
        if module_path.suffix == '.py':
            pyfiles = {module_path}
        else:
            pyfiles = set()

    excluded = set(f for excluded_module in excluded_modules
                   for f in glob.glob(excluded_module, recursive=True))

    yield from (Path(pyfile) for pyfile in pyfiles - excluded)
