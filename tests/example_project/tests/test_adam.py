"Tests for the adam packages."

# pylint: disable=C0111

import copy
import uuid
import unittest

import adam.adam_1
import adam.adam_2


class Tests(unittest.TestCase):
    def test_constant_number(self):
        self.assertEqual(adam.adam_1.constant_number(), 42)

    def test_constant_true(self):
        self.assertEqual(adam.adam_1.constant_true(), True)

    def test_constant_false(self):
        self.assertEqual(adam.adam_1.constant_false(), False)

    def test_bool_and(self):
        self.assertFalse(adam.adam_1.bool_and())

    def test_bool_or(self):
        self.assertTrue(adam.adam_1.bool_or())

    def test_bool_expr_with_not(self):
        self.assertFalse(adam.adam_1.bool_expr_with_not())

    def test_bool_if(self):
        self.assertTrue(adam.adam_1.bool_if())

    def test_if_expression(self):
        self.assertTrue(adam.adam_1.if_expression())

    def test_assert_in_func(self):
        self.assertTrue(adam.adam_1.assert_in_func())

    def test_unary_sub(self):
        self.assertEqual(adam.adam_1.unary_sub(), -1)

    def test_unary_add(self):
        self.assertEqual(adam.adam_1.unary_add(), +1)

    def test_binary_add(self):
        self.assertEqual(adam.adam_1.binary_add(), 11)

    def test_equals(self):
        vals = [uuid.uuid4(), uuid.uuid4()]
        vals.append(copy.copy(vals[0]))
        self.assertTrue(adam.adam_1.equals(vals))

    def test_break_to_continue(self):
        self.assertEqual(adam.adam_1.use_break(10), 0)

    def test_continue_to_break(self):
        self.assertEqual(adam.adam_1.use_continue(10), 9)

    def test_trigger_infinite_loop(self):
        self.assertTrue(adam.adam_2.trigger_infinite_loop())

    def test_single_iteration(self):
        self.assertTrue(adam.adam_2.single_iteration())

    def test_handle_exception(self):
        self.assertTrue(adam.adam_2.handle_exception())

    def test_decorator(self):
        self.assertTrue(adam.adam_2.decorated_func())

    def test_use_cffi(self):
        assert adam.adam_2.use_ctypes(1000000) == b'b' * 1000000
