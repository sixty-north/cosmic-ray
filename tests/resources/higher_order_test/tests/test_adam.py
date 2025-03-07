"""Tests for the adam module."""

import unittest

from adam import add_and_compare, check_logic


class TestAdam(unittest.TestCase):
    """Tests for functions in the adam module."""

    def test_add_and_compare(self):
        """Test the add_and_compare function."""
        self.assertEqual(add_and_compare(2, 3, 4), "Greater")
        self.assertEqual(add_and_compare(2, 3, 6), "Less")
        self.assertEqual(add_and_compare(2, 3, 5), "Equal")

    def test_check_logic(self):
        """Test the check_logic function."""
        self.assertEqual(check_logic(True, True), "Both")
        self.assertEqual(check_logic(True, False), "At least one")
        self.assertEqual(check_logic(False, True), "At least one")
        self.assertEqual(check_logic(False, False), "None")
