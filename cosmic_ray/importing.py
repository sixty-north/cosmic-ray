"""Functionality related to Python's import mechanisms.
"""

from itertools import islice
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
