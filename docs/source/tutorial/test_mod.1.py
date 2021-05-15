import unittest
import mod


class Tests(unittest.TestCase):
    def test_func(self):
        self.assertEqual(mod.func(), 1234)