from cosmic_ray.mutating import apply_mutation
from cosmic_ray.operators.binary_operator_replacement import ReplaceBinaryOperator_Mul_Add


def test_import_star_not_mutated_as_binary_operator(tmp_path):
    module = tmp_path / "module.py"
    module.write_text("from math import *")
    _, mutated = apply_mutation(module, ReplaceBinaryOperator_Mul_Add(), 0)
    assert mutated is None

    
