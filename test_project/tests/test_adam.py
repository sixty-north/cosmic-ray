import copy
import uuid
import unittest

import adam


class Tests(unittest.TestCase):
    def test_constant_number(self):
        self.assertEqual(
            adam.constant_number(),
            42)

    def test_constant_true(self):
        self.assertEqual(
            adam.constant_true(),
            True)

    def test_constant_false(self):
        self.assertEqual(
            adam.constant_false(),
            False)

    def test_bool_and(self):
        self.assertFalse(adam.bool_and())

    def test_bool_or(self):
        self.assertTrue(adam.bool_or())

    def test_bool_expr_with_not(self):
        self.assertFalse(adam.bool_expr_with_not())

    def test_bool_if(self):
        self.assertTrue(adam.bool_if())

    def test_if_expression(self):
        self.assertTrue(adam.if_expression())

    def test_assert_in_func(self):
        self.assertTrue(adam.assert_in_func())

    def test_unary_sub(self):
        self.assertEqual(
            adam.unary_sub(),
            -1)

    def test_unary_add(self):
        self.assertEqual(
            adam.unary_add(),
            +1)

    def test_binary_add(self):
        self.assertEqual(adam.binary_add(), 11)

    def test_equals(self):
        vals = [uuid.uuid1(),
                uuid.uuid1()]
        vals.append(copy.copy(vals[0]))
        self.assertTrue(
            adam.equals(vals))

    def test_break_to_continue(self):
        self.assertEqual(
            adam.use_break(10),
            0)

    def test_continue_to_break(self):
        self.assertEqual(
            adam.use_continue(10),
            9)

    def test_trigger_infinite_loop(self):
        self.assertTrue(adam.trigger_infinite_loop())

    def test_single_iteration(self):
        self.assertTrue(adam.single_iteration())

    def test_handle_exception(self):
        self.assertTrue(adam.handle_exception())

    def test_decorator(self):
        self.assertTrue(adam.decorated_func())
