from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec


class ASTLoader:
    def __init__(self, ast):
        self._ast = ast

    @property
    def source_code(self):
        return generate_source_code(self._ast)

    def exec_module(self, mod):
        exec(self.source_code,
             mod.__dict__)


class Finder(MetaPathFinder, dict):
    """A finder that returns an ASTLoader when one of its keys matches the
    module name.

    """
    def find_spec(self, fullname, path, target=None):
        try:
            return ModuleSpec(fullname,
                              ASTLoader(self[fullname]))
