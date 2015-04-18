import copy
import uuid
import unittest

import adam


class Tests(unittest.TestCase):
    # def test_constant_number(self):
    #     self.assertEqual(
    #         adam.constant_number(),
    #         42)

    # def test_unary_sub(self):
    #     self.assertEqual(
    #         adam.unary_sub(),
    #         -1)

    # def test_unary_add(self):
    #     self.assertEqual(
    #         adam.unary_add(),
    #         +1)

    def test_equals(self):
        vals = [uuid.uuid1(),
                uuid.uuid1()]
        vals.append(copy.copy(vals[0]))
        self.assertTrue(
            adam.equals(vals))
