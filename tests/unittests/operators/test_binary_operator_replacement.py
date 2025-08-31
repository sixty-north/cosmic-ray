from cosmic_ray.mutating import mutate_code
from cosmic_ray.operators.binary_operator_replacement import (
    ReplaceBinaryOperator_Add_Mul,
    ReplaceBinaryOperator_BitOr_Add,
    ReplaceBinaryOperator_Mul_Add,
    ReplaceBinaryOperator_Sub_Add,
)


def test_pipe_operator_in_assignment_annotation_not_mutated_as_binary_operator():
    code = "my_var: str | int = 10"
    mutated = mutate_code(code, ReplaceBinaryOperator_BitOr_Add(), 0)
    assert mutated is None


def test_pipe_operator_in_local_assignment_annotation_not_mutated_as_binary_operator():
    code = r"""
def my_function():
    local_var: str | int = 3
"""
    mutated = mutate_code(code, ReplaceBinaryOperator_BitOr_Add(), 0)
    assert mutated is None


def test_pipe_in_function_argument_type_annotation_mutated_as_binary_operator():
    code = r"""
def my_function(arg: str | int = 10):
    local_var = arg
"""
    mutated = mutate_code(code, ReplaceBinaryOperator_BitOr_Add(), 0)
    assert mutated is not None


def test_bitwise_or_mutated_as_binary_operator():
    code = "my_var = 10 | 2"
    mutated = mutate_code(code, ReplaceBinaryOperator_BitOr_Add(), 0)
    assert mutated is not None


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
