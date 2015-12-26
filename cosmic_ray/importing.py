"""Functionality related to Python's import mechanisms.
"""

import contextlib
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
import sys


class ASTLoader:  # pylint:disable=old-style-class,too-few-public-methods
    """An `importlib.abc.Loader` which loads an AST for a particular name.

    You construct this with an AST and a module name. The
    `exec_module` method simply compiles the AST with the name and
    execs the resulting code against the provided module dict.

    In practice, this is how cosmic-ray loads mutated ASTs for modules.
    """
    def __init__(self, ast, name):
        self._ast = ast
        self._name = name

    def exec_module(self, mod):
        exec(compile(self._ast, self._name, 'exec'),  # pylint:disable=exec-used
             mod.__dict__)


class ASTFinder(MetaPathFinder):  # pylint:disable=too-few-public-methods
    """An `importlib.ast.MetaPathFinder` that associates a module name
    with an AST.

    Construct this by passing a module name and associated AST. When
    the finder is asked for that name, it will return a loader that
    produces the code equivalent of the AST.

    We use this to inject mutated ASTs into tests.
    """
    def __init__(self, fullname, ast):
        self._fullname = fullname
        self._ast = ast

    def find_spec(self, fullname, path, target=None):  # pylint:disable=unused-argument
        if fullname == self._fullname:
            return ModuleSpec(fullname,
                              ASTLoader(self._ast, fullname))
        else:
            return None


@contextlib.contextmanager
def using_mutant(module_name, mutant):
    """Create a new Finder as a context-manager.

    This creates a new Finder which loads the AST `mutant` when `module_name`
    is requested. It installs this finder at the head of `sys.meta_path` for
    the duration of the with-block, yielding the Finder in the with-statement.
    After the with-block, the Finder is uninstalled.

    This also removes `module_name` from `sys.modules` before doing
    anything else. Then ensures that the finder gets asked to load the
    mutated AST.

    """
    if module_name in sys.modules:
        del sys.modules[module_name]

    finder = ASTFinder(module_name, mutant)
    sys.meta_path = [finder] + sys.meta_path
    try:
        yield finder
    finally:
        sys.meta_path.remove(finder)
