import ast
import unittest

from cosmic_ray.util import get_line_number


class Tests(unittest.TestCase):
    def test_basic(self):
        code = 'if x == 1:' \
               '    return 3'
        tree = ast.parse(code)
        self.assertEqual(
            get_line_number(tree),
            '<UNKNOWN>')
        self.assertEqual(
            get_line_number(
                tree.body[0]),
            1)
        self.assertEqual(
            get_line_number(
                tree.body[0].test),
            1)
        self.assertEqual(
            get_line_number(
                tree.body[0].test.ops[0]),
            '<UNKNOWN>')
