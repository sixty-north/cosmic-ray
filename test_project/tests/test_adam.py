import unittest
import adam


class Tests(unittest.TestCase):
    def test_get_negative_one(self):
        self.assertEqual(
            adam.get_negative_one(),
            -1)

    def test_get_positive_one(self):
        self.assertEqual(
            adam.get_positive_one(),
            +1)
