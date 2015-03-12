import unittest
import adam


class Tests(unittest.TestCase):
    def test_add_numbers(self):
        self.assertEqual(
            adam.add_numbers(),
            2)
