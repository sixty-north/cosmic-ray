import ast
import importlib
import sys
import unittest

from cosmic_ray.importing import Finder


class TestFinder(unittest.TestCase):
    def setUp(self):
        self.finder = Finder()
        code = 'def foo(): return 42'
        node = ast.parse(code)

        self.module_name = 'cosmic_ray.test.finder_test_validation_module'
        self.finder[self.module_name] = node
        sys.meta_path = [self.finder] + sys.meta_path

    def tearDown(self):
        try:
            sys.meta_path.remove(self.finder)
        except ValueError:
            # This means a test somehow removed the finder.
            pass

    def test_finder_imports_ast_based_module(self):
        mod = importlib.import_module(self.module_name)
        self.assertEqual(mod.foo(), 42)

    def test_imports_fail_when_finder_is_removed(self):
        sys.meta_path.remove(self.finder)
        sys.modules.pop(self.module_name, None)

        with self.assertRaises(ImportError):
            importlib.import_module(self.module_name)
