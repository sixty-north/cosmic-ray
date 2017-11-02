"""Functionality related to Python's import mechanisms."""

import contextlib
import sys
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec


class ASTLoader:  # pylint:disable=old-style-class,too-few-public-methods

    """
    An `importlib.abc.Loader` which loads an AST for a particular name.

    You construct this with an AST and a module name. The
    `exec_module` method simply compiles the AST with the name and
    execs the resulting code against the provided module dict.

    In practice, this is how cosmic-ray loads mutated ASTs for modules.
    """

    def __init__(self, ast, name):
        self._ast = ast
        self._name = name

    def create_module(self,  # pylint: disable=no-self-use
                      spec):  # pylint: disable=unused-argument
        return None

    def exec_module(self, mod):
        compiled = compile(self._ast, self._name, 'exec')
        exec(compiled, mod.__dict__)  # pylint:disable=exec-used


class ASTFinder(MetaPathFinder):  # pylint:disable=too-few-public-methods

    """
    An `importlib.ast.MetaPathFinder` that associates a module name
    with an AST.

    Construct this by passing a module name and associated AST. When
    the finder is asked for that name, it will return a loader that
    produces the code equivalent of the AST.

    We use this to inject mutated ASTs into tests.
    """

    def __init__(self, fullname, ast):
        self._fullname = fullname
        self._ast = ast

    def find_spec(self, fullname,
                  path, target=None):  # pylint:disable=unused-argument
        if fullname == self._fullname:
            return ModuleSpec(fullname,
                              ASTLoader(self._ast, fullname))


@contextlib.contextmanager
def preserve_modules():
    """Remember the state of sys.modules on enter and reset it on exit.
    """
    original_mods = dict(sys.modules)
    try:
        yield
    finally:
        del_mods = {m for m in sys.modules if m not in original_mods}
        for mod in del_mods:
            del sys.modules[mod]


@contextlib.contextmanager
def using_ast(module_name, module_ast):
    """Create a new Finder as a context-manager.

    This creates a new Finder which loads the AST `module_ast` when
    `module_name` is requested. It installs this finder at the head of
    `sys.meta_path` for the duration of the with-block, yielding the Finder in
    the with-statement. After the with-block, the Finder is uninstalled.

    Note that this does *not* attempt to adjust `sys.modules` in any way. You
    should make sure to clear out any existing references to `module_name`
    before running this (e.g. with `preserve_modules()` or something similar).

    """
    finder = ASTFinder(module_name, module_ast)
    sys.meta_path = [finder] + sys.meta_path
    try:
        yield finder
    finally:
        sys.meta_path.remove(finder)
