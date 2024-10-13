"""Tests for the various mutation operators."""

import parso
import pytest

from cosmic_ray.mutating import MutationVisitor
from cosmic_ray.operators.binary_operator_replacement import ReplaceBinaryOperator_Add_Mul
from cosmic_ray.operators.operator import Example
from cosmic_ray.operators.unary_operator_replacement import ReplaceUnaryOperator_USub_UAdd
from cosmic_ray.operators.variable_inserter import VariableInserter
from cosmic_ray.operators.variable_replacer import VariableReplacer
from cosmic_ray.plugins import get_operator, operator_names


class Sample:
    def __init__(self, operator, example):
        self.operator = operator
        self.example = example


OPERATOR_PROVIDED_SAMPLES = tuple(
    Sample(operator_class, example)
    for operator_class in map(get_operator, operator_names())
    for example in operator_class.examples()
)

EXTRA_SAMPLES = tuple(
    Sample(*args)
    for args in (
        # Make sure unary and binary op mutators don't pick up the wrong kinds of operators
        (ReplaceUnaryOperator_USub_UAdd, Example("x + 1", "x + 1")),
        (ReplaceBinaryOperator_Add_Mul, Example("+1", "+1")),
    )
)

OPERATOR_SAMPLES = OPERATOR_PROVIDED_SAMPLES + EXTRA_SAMPLES


@pytest.mark.parametrize("sample", OPERATOR_SAMPLES, ids=lambda s: str(s.operator.__name__))
def test_mutation_changes_ast(sample: Sample):
    if sample.operator in {VariableReplacer, VariableInserter}:
        pytest.xfail(f"{sample.operator} tests fail because they produce random output.")

    node = parso.parse(sample.example.pre_mutation_code)
    visitor = MutationVisitor(sample.example.occurrence, sample.operator(**sample.example.operator_args))
    mutant = visitor.walk(node)

    assert mutant.get_code() == sample.example.post_mutation_code


@pytest.mark.parametrize("sample", OPERATOR_SAMPLES)
def test_no_mutation_leaves_ast_unchanged(sample):
    print(sample.operator, sample.example)
    node = parso.parse(sample.example.pre_mutation_code)
    visitor = MutationVisitor(-1, sample.operator(**sample.example.operator_args))
    mutant = visitor.walk(node)

    assert mutant.get_code() == sample.example.pre_mutation_code
