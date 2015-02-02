import sys

from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec


class Loader:
    def exec_module(self, mod):
        print('Loading synthetic module!')
        exec('''
def foobar():
        return "foobar"
''',
             mod.__dict__)


class Finder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == 'synthetic':
            print('Found request for synthetic module!')
            return ModuleSpec(fullname, Loader())


# Add our synthetic loader to the front
sys.meta_path = [Finder()] + sys.meta_path

try:
    del sys.modules['synthetic']
except KeyError:
    pass

import synthetic
