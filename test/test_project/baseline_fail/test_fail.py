import unittest

from eve import eve


class Tests(unittest.TestCase):
    def test_constant_42(self):
        # NOTE: this should always fail b/c we need to verify
        # that Cosmic Ray exits with non zero when baseline fails!
        # see https://github.com/sixty-north/cosmic-ray/issues/111
        self.assertEqual(eve.constant_42(), 0)
