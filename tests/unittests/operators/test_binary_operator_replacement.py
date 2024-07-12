from cosmic_ray.mutating import mutate_code
from cosmic_ray.operators.binary_operator_replacement import (
    ReplaceBinaryOperator_Mul_Add,
    ReplaceBinaryOperator_Sub_Add,
    ReplaceBinaryOperator_Add_Mul,
)


def test_import_star_not_mutated_as_binary_operator():
    code = "from math import *"
    mutated = mutate_code(code, ReplaceBinaryOperator_Mul_Add(), 0)
    assert mutated is None


def test_star_expr_not_mutated_as_binary_operator():
    code = "a, *b = x"
    mutated = mutate_code(code, ReplaceBinaryOperator_Mul_Add(), 0)
    assert mutated is None


def test_star_args_not_mutated_as_binary_operator():
    code = "def foo(*args): pass"
    mutated = mutate_code(code, ReplaceBinaryOperator_Mul_Add(), 0)
    assert mutated is None


def test_unary_minus_not_mutated_as_binary_operator():
    code = "-1"
    mutated = mutate_code(code, ReplaceBinaryOperator_Sub_Add(), 0)
    assert mutated is None


def test_unary_plus_not_mutated_as_binary_operator():
    code = "+1"
    mutated = mutate_code(code, ReplaceBinaryOperator_Add_Mul(), 0)
    assert mutated is None
