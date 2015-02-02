import unittest

import mod


class Tests(unittest.TestCase):
    def test_simple(self):
        self.assertTrue(
            mod.foo())
