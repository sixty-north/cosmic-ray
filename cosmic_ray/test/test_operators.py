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
from cosmic_ray.mutating import MutatingCore


class Linearizer(ast.NodeVisitor):
    """A NodeVisitor which builds a linear list of nodes it visits.

    The basic point is to be able to take a tree of nodes and reproducably
    construct a simple list. This list is useful for e.g. comparison between
    trees.

    After using this to visit an AST, the `nodes` attribute holds the list of
    nodes.
    """
    def __init__(self):
        self.nodes = []

    def generic_visit(self, node):
        self.nodes.append(node)
        super().generic_visit(node)


def linearize_tree(node):
    "Given an AST, return a list of the nodes therein."
    l = Linearizer()
    l.visit(node)
    return l.nodes


class MutationTextMixin:
    """A set of mutation-oriented tests for `Operators`.

    This is designed to be used as a mixin with `unittest.TestCase`. That is,
    if you subclass from both this and `TestCase` then this will provide actual
    test functions. The tests are all oriented to testing whether the operator
    behaves correctly when supplied with a MutatingCore.

    Each subclass of this must provide two functions:
    - source(): returns a body of code on which the operator can function.
    - operator(): returns an `Operator` class object.
    """
    def test_activation_record_created(self):
        node = ast.parse(self.code())
        core = MutatingCore(0)
        op = self.operator()(core)
        self.assertFalse(core.activation_record)
        op.visit(node)
        self.assertTrue(core.activation_record)

    def test_no_activation_record_created(self):
        node = ast.parse(self.code())
        core = MutatingCore(1)
        op = self.operator()(core)
        op.visit(node)
        self.assertFalse(core.activation_record)

    def test_mutation_changes_ast(self):
        node = ast.parse(self.code())
        core = MutatingCore(0)
        mutant = self.operator()(core).visit(copy.deepcopy(node))

        orig_nodes = linearize_tree(node)
        mutant_nodes = linearize_tree(mutant)

        self.assertEqual(len(orig_nodes),
                         len(mutant_nodes))

        self.assertNotEqual(
            ast.dump(node),
            ast.dump(mutant))

    def test_no_mutation_leaves_ast_unchanged(self):
        node = ast.parse(self.code())

        core = MutatingCore(1)
        replacer = self.operator()(core)
        self.assertEqual(
            ast.dump(node),
            ast.dump(replacer.visit(copy.deepcopy(node))))


class CountingTextMixin:
    """A set of counting-oriented tests for `Operators`.

    This is designed to be used as a mixin with `unittest.TestCase`. That is,
    if you subclass from both this and `TestCase` then this will provide actual
    test functions. The tests are all oriented to testing whether the operator
    behaves correctly when supplied with a CountingCore.

    Each subclass of this must provide two functions:
    - source(): returns a body of code on which the operator can function.
    - operator(): returns an `Operator` class object.
    """
    def test_replacement_activated_core(self):
        node = ast.parse(self.code())
        core = _CountingCore()
        op = self.operator()(core)
        op.visit(node)
        self.assertEqual(core.count, 1)


class TestReplaceBreakWithContinue(unittest.TestCase,
                                   MutationTextMixin,
                                   CountingTextMixin):
    def code(self):
        return 'while True: break'

    def operator(self):
        return ReplaceBreakWithContinue


class TestReplaceContinueWithBreak(unittest.TestCase,
                                   MutationTextMixin,
                                   CountingTextMixin):
    def code(self):
        return 'while False: continue'

    def operator(self):
        return ReplaceContinueWithBreak


class TestNumberReplacer(unittest.TestCase,
                         MutationTextMixin,
                         CountingTextMixin):
    def code(self):
        return 'x = 1'

    def operator(self):
        return NumberReplacer


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


class test_ReplaceRelationalOp(unittest.TestCase):
    def test_ast_node_is_modified(self):
        for replacer in ROR.OPERATORS:
            code = RELATIONAL_OP_MAP[replacer.from_op]
            node = ast.parse(code)
            self.assertIsInstance(
                node.body[0].test.ops[0],
                replacer.from_op)

        core = MutatingCore(0)
        node = replacer(core).visit(node)
        self.assertNotIsInstance(
            node.body[0].test.ops[0],
            replacer.from_op)
