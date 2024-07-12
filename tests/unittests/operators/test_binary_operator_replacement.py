from cosmic_ray.mutating import apply_mutation
from cosmic_ray.operators.binary_operator_replacement import (
    ReplaceBinaryOperator_Mul_Add,
    ReplaceBinaryOperator_Sub_Add,
    ReplaceBinaryOperator_Add_Mul,
)


def test_import_star_not_mutated_as_binary_operator(tmp_path):
    module = tmp_path / "module.py"
    module.write_text("from math import *")
    _, mutated = apply_mutation(module, ReplaceBinaryOperator_Mul_Add(), 0)
    assert mutated is None


def test_star_expr_not_mutated_as_binary_operator(tmp_path):
    module = tmp_path / "module.py"
    module.write_text("a, *b = x")
    _, mutated = apply_mutation(module, ReplaceBinaryOperator_Mul_Add(), 0)
    assert mutated is None


def test_star_args_not_mutated_as_binary_operator(tmp_path):
    module = tmp_path / "module.py"
    module.write_text("def foo(*args): pass")
    _, mutated = apply_mutation(module, ReplaceBinaryOperator_Mul_Add(), 0)
    assert mutated is None


def test_unary_minus_not_mutated_as_binary_operator(tmp_path):
    module = tmp_path / "module.py"
    module.write_text("-1")
    _, mutated = apply_mutation(module, ReplaceBinaryOperator_Sub_Add(), 0)
    assert mutated is None


def test_unary_plus_not_mutated_as_binary_operator(tmp_path):
    module = tmp_path / "module.py"
    module.write_text("+1")
    _, mutated = apply_mutation(module, ReplaceBinaryOperator_Add_Mul(), 0)
    assert mutated is None
