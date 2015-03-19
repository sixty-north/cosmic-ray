import unittest
import adam


class Tests(unittest.TestCase):
    def test_unary_sub(self):
        self.assertEqual(
            adam.unary_sub(),
            -1)

    def test_unary_add(self):
        self.assertEqual(
            adam.unary_add(),
            +1)

    def test_equals(self):
        self.assertTrue(adam.equals())
