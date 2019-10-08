"""Tests for the various mutation operators.
"""
import pytest

import parso

from cosmic_ray.plugins import get_operator, operator_names
from cosmic_ray.operators.unary_operator_replacement import ReplaceUnaryOperator_USub_UAdd
from cosmic_ray.operators.binary_operator_replacement import ReplaceBinaryOperator_Add_Mul
from cosmic_ray.mutating import MutationVisitor


class Sample:
    def __init__(self, operator, from_code, to_code, index=0, config=None):
        self.operator = operator
        self.from_code = from_code
        self.to_code = to_code
        self.index = index
        self.config = config


OPERATOR_PROVIDED_SAMPLES = tuple(
    Sample(operator_class, *example)
    for operator_class in map(get_operator, operator_names())
    for example in operator_class.examples()
)

EXTRA_SAMPLES = tuple(
    Sample(*args) for args in (
        # Make sure unary and binary op mutators don't pick up the wrong kinds of operators
        (ReplaceUnaryOperator_USub_UAdd, 'x + 1', 'x + 1'),
        (ReplaceBinaryOperator_Add_Mul, '+1', '+1'),
    ))

OPERATOR_SAMPLES = OPERATOR_PROVIDED_SAMPLES + EXTRA_SAMPLES


@pytest.mark.parametrize('sample', OPERATOR_SAMPLES)
def test_mutation_changes_ast(sample, python_version):
    node = parso.parse(sample.from_code)
    visitor = MutationVisitor(sample.index, sample.operator(python_version, sample.config))
    mutant = visitor.walk(node)

    assert mutant.get_code() == sample.to_code


@pytest.mark.parametrize('sample', OPERATOR_SAMPLES)
def test_no_mutation_leaves_ast_unchanged(sample, python_version):
    node = parso.parse(sample.from_code)
    visitor = MutationVisitor(-1, sample.operator(python_version, sample.config))
    mutant = visitor.walk(node)

    assert mutant.get_code() == sample.from_code
