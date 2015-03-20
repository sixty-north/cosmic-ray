import unittest
import adam


class Tests(unittest.TestCase):
    # TODO: Without this test, the adam tests should have a
    # survivor. However, all are killed. It appears that modules are
    # still not being replaced properly. Ugh.s

    def test_constant_number(self):
        self.assertEqual(
            adam.constant_number(),
            42)

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
