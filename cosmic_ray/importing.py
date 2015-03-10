"""Functionality related to Python's import mechanisms.
"""

import ast
import contextlib
import logging
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
import sys

from .find_modules import find_modules
from .util import isolate_import_environment

log = logging.getLogger()


class ASTLoader:
    def __init__(self, ast, name):
        self._ast = ast
        self._name = name

    def exec_module(self, mod):
        exec(compile(self._ast, self._name, 'exec'),
             mod.__dict__)


class Finder(MetaPathFinder, dict):
    """A finder that returns an ASTLoader when one of its keys matches the
    module name.

    """
    def find_spec(self, fullname, path, target=None):
        try:
            return ModuleSpec(fullname,
                              ASTLoader(self[fullname], fullname))
        except KeyError:
            pass

    def __repr__(self):
        return '{}'.format(self.__class__)


@isolate_import_environment
def create_finder(module_name):
    """Create an `importing.Finder` with one entry for each submodule in
    `module_name`, including `module_name` itself.
    """
    finder = Finder()

    for module in find_modules(module_name):
        with open(module.__file__, 'rt') as f:
            log.info('Reading module {} from {}'.format(
                module.__name__, module.__file__))
            source = f.read()

        log.info('Parsing module {}'.format(module.__name__))

        finder[module.__name__] = ast.parse(
            source, module.__file__, 'exec')

    return finder


@contextlib.contextmanager
def install_finder(module_name):
    """Create a new Finder as a context-manager.

    This installs the finder for the duration of the with-block,
    yielding the Finder in the with-statement. After the with-block,
    the Finder is uninstalled.
    """
    finder = create_finder(module_name)
    sys.meta_path = [finder] + sys.meta_path
    try:
        yield finder
    except Exception:
        sys.meta_path.remove(finder)
        raise
