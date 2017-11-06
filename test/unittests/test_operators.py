"""Tests for the various mutation operators.
"""
import ast
import copy
import pytest

from cosmic_ray.operators.comparison_operator_replacement import \
    MutateComparisonOperator
from cosmic_ray.operators.unary_operator_replacement import \
    MutateUnaryOperator
from cosmic_ray.operators.binary_operator_replacement import \
    MutateBinaryOperator
from cosmic_ray.counting import _CountingCore
from cosmic_ray.operators.boolean_replacer import (ReplaceTrueFalse,
                                                   ReplaceAndWithOr,
                                                   ReplaceOrWithAnd,
                                                   AddNot)
from cosmic_ray.operators.break_continue import (ReplaceBreakWithContinue,
                                                 ReplaceContinueWithBreak)
from cosmic_ray.operators.exception_replacer import ExceptionReplacer
from cosmic_ray.operators.number_replacer import NumberReplacer
from cosmic_ray.operators.remove_decorator import RemoveDecorator
from cosmic_ray.operators.zero_iteration_loop import ZeroIterationLoop
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


OPERATOR_SAMPLES = [
    (ReplaceTrueFalse, 'True'),
    (ReplaceAndWithOr, 'if True and False: pass'),
    (ReplaceOrWithAnd, 'if True or False: pass'),
    (AddNot, 'if True or False: pass'),
    (AddNot, 'A if B else C'),
    (AddNot, 'assert isinstance(node, ast.Break)'),
    (AddNot, 'while True: pass'),
    (ReplaceBreakWithContinue, 'while True: break'),
    (ReplaceContinueWithBreak, 'while False: continue'),
    (NumberReplacer, 'x = 1'),
    (MutateComparisonOperator, 'if x > y: pass'),
    (MutateUnaryOperator, 'return not X'),
    (MutateUnaryOperator, 'x = -1'),
    (MutateBinaryOperator, 'x * y'),
    (MutateBinaryOperator, 'x - y'),
    (ExceptionReplacer, 'try: raise OSError \nexcept OSError: pass'),
    (ZeroIterationLoop, 'for i in range(1,2): pass'),
    (RemoveDecorator, 'def wrapper(f): f.cosmic_ray=1; '
                      'return f\n@wrapper\ndef foo(): pass')
]


@pytest.mark.parametrize('operator,code', OPERATOR_SAMPLES)
def test_activation_record_created(operator, code):
    node = ast.parse(code)
    core = MutatingCore(0)
    op = operator(core)
    assert core.activation_record is None
    op.visit(node)
    assert core.activation_record is not None


@pytest.mark.parametrize('operator,code', OPERATOR_SAMPLES)
def test_no_activation_record_created(operator, code):
    node = ast.parse(code)
    core = MutatingCore(-1)
    op = operator(core)
    op.visit(node)
    assert core.activation_record is None


@pytest.mark.parametrize('operator,code', OPERATOR_SAMPLES)
def test_mutation_changes_ast(operator, code):
    node = ast.parse(code)
    core = MutatingCore(0)
    mutant = operator(core).visit(copy.deepcopy(node))

    orig_nodes = linearize_tree(node)  # noqa
    mutant_nodes = linearize_tree(mutant)  # noqa

    # todo: disabled b/c adding/removing the not keyword
    # changes the number of nodes in the tree.
    #    assert len(orig_nodes) == len(mutant_nodes)

    assert ast.dump(node) != ast.dump(mutant)


@pytest.mark.parametrize('operator,code', OPERATOR_SAMPLES)
def test_no_mutation_leaves_ast_unchanged(operator, code):
    node = ast.parse(code)

    core = MutatingCore(-1)
    replacer = operator(core)
    assert ast.dump(node) == ast.dump(replacer.visit(copy.deepcopy(node)))


@pytest.mark.parametrize('operator,code', OPERATOR_SAMPLES)
def test_replacement_activated_core(operator, code):
    node = ast.parse(code)
    core = _CountingCore()
    op = operator(core)
    op.visit(node)
    assert core.count >= 1
