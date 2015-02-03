"""Functionality related to Python's import mechanisms.
"""

from itertools.import islice
import sys

from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec


class ASTLoader:
    def __init__(self, ast, name):
        self._ast = ast
        self._name = name

    def exec_module(self, mod):
        exec(compile(self._ast, self.name, 'exec'),
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


def enable_ast_loading():
    """Ensure that a `Finder` is installed on `sys.meta_path`.

    This has the effect of allowing imports via any AST tree managed
    by the `Finder`.

    If no `Finder` instance is found in `sys.meta_path`, a new one is
    created, prepended to `sys.meta_path`, and returned.

    If there are one more more `Finder` instances in `sys.meta_path`,
    the first on in the list is returned.
    """
    try:
        finder = [f for f in sys.meta_path if isinstance(f, Finder)][0]
    except IndexError:
        finder = Finder()
        sys.meta_path = [finder] + sys.meta_path

    return finder


def disable_ast_loading():
    """Remove all instances of `Finder` from `sys.meta_path`.

    This has the effect of preventing importing via AST nodes.
    """
    sys.meta_path = [f for f in sys.meta_path if not isinstance(f, Finder)]
