"""Tests for the various mutation operators.
"""

import ast
import copy
import unittest

import cosmic_ray.operators.relational_operator_replacement as ROR
from cosmic_ray.counting import _CountingCore
from cosmic_ray.operators.break_continue import (ReplaceBreakWithContinue,
                                                 ReplaceContinueWithBreak)
from cosmic_ray.operators.number_replacer import NumberReplacer
from cosmic_ray.operators.operator import MutatingCore


class Linearizer(ast.NodeVisitor):
    def __init__(self):
        self.nodes = []

    def generic_visit(self, node):
        self.nodes.append(node)
        super().generic_visit(node)


def linearize_tree(node):
    l = Linearizer()
    l.visit(node)
    return l.nodes


class TestReplaceBreakWithContinueMutation(unittest.TestCase):
    def test_replacement_activated_replacer(self):
        node = ast.parse('while True: break')
        core = MutatingCore(0)
        replacer = ReplaceBreakWithContinue(core)
        replacer.visit(node)
        self.assertTrue(core.activation_record)

    def test_remove_first(self):
        node = ast.parse('while True: break')
        core = MutatingCore(0)
        mutant = ReplaceBreakWithContinue(core).visit(copy.deepcopy(node))

        orig_nodes = linearize_tree(node)
        mutant_nodes = linearize_tree(mutant)

        self.assertEqual(len(orig_nodes),
                         len(mutant_nodes))

        self.assertNotEqual(
            ast.dump(node),
            ast.dump(mutant))


class TestReplaceBreakWithContinueCounting(unittest.TestCase):
    def test_replacement_activated_core(self):
        node = ast.parse('while True: break')
        core = _CountingCore()
        replacer = ReplaceBreakWithContinue(core)
        replacer.visit(node)
        self.assertEqual(core.count, 1)


class TestReplaceContinueWithBreakMutating(unittest.TestCase):
    def test_replacement_activated_replacer(self):
        node = ast.parse('while False: continue')
        core = MutatingCore(0)
        replacer = ReplaceContinueWithBreak(core)
        replacer.visit(node)
        self.assertTrue(core.activation_record)

    def test_remove_first(self):
        node = ast.parse('while False: continue')
        core = MutatingCore(0)
        mutant = ReplaceContinueWithBreak(core).visit(copy.deepcopy(node))

        orig_nodes = linearize_tree(node)
        mutant_nodes = linearize_tree(mutant)

        self.assertEqual(len(orig_nodes),
                         len(mutant_nodes))

        self.assertNotEqual(
            ast.dump(node),
            ast.dump(mutant))


class TestReplaceContinueWithBreakCounting(unittest.TestCase):
    def test_replacement_activated_core(self):
        node = ast.parse('while False: continue')
        core = _CountingCore()
        replacer = ReplaceContinueWithBreak(core)
        replacer.visit(node)
        self.assertEqual(core.count, 1)


class TestNumberReplacer(unittest.TestCase):
    def test_replacement_activated_replacer(self):
        node = ast.parse('x = 1')
        core = MutatingCore(0)
        replacer = NumberReplacer(core)
        replacer.visit(node)
        self.assertTrue(core.activation_record)

    def test_remove_first(self):
        node = ast.parse('x = 1')
        core = MutatingCore(0)
        mutant = NumberReplacer(core).visit(copy.deepcopy(node))

        orig_nodes = linearize_tree(node)
        mutant_nodes = linearize_tree(mutant)

        self.assertEqual(len(orig_nodes),
                         len(mutant_nodes))

        self.assertNotEqual(
            ast.dump(node),
            ast.dump(mutant))

    def test_non_replacement_does_not_activate_replacer(self):
        node = ast.parse('x = 1')
        core = MutatingCore(1)
        replacer = NumberReplacer(core)
        replacer.visit(node)
        self.assertFalse(core.activation_record)

    def test_replacer_ignore_non_nth_sites(self):
        node = ast.parse('x = 1')

        core = MutatingCore(1)
        replacer = NumberReplacer(core)
        self.assertEqual(
            ast.dump(node),
            ast.dump(replacer.visit(copy.deepcopy(node))))

RELATIONAL_OP_MAP = {op: 'if x {} 1: pass'.format(token)
                     for op, token in {
                         ast.Eq: '==',
                         ast.NotEq: '!=',
                         ast.Lt: '<',
                         ast.LtE: '<=',
                         ast.Gt: '>',
                         ast.GtE: '>=',
                         ast.Is: 'is',
                         ast.IsNot: 'is not',
                         ast.In: 'in',
                         ast.NotIn: 'not in'
                         }.items()}


@unittest.skip('reenable me!')
class test_ReplaceRelationalOp(unittest.TestCase):
    def test_ast_node_is_modified(self):
        for replacer in ROR.OPERATORS:
            code = RELATIONAL_OP_MAP[replacer.from_op]
            node = ast.parse(code)
            self.assertIsInstance(
                node.body[0].test.ops[0],
                replacer.from_op)

        node = replacer(0).visit(node)
        self.assertNotIsInstance(
            node.body[0].test.ops[0],
            replacer.from_op)
