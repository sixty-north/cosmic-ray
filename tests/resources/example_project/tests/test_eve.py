import unittest

from eve import eve


class Tests(unittest.TestCase):
    def test_constant_42(self):
        self.assertEqual(eve.constant_42(), 42)
