import ast

from cosmic_ray.util import build_mutations


OPERATORS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
             ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor,
             ast.BitAnd)


def to_ops(f):
    return OPERATORS + (None,)


def test_build_mutations_avoids_self_mutations():
    for idx, to_op in build_mutations(OPERATORS, to_ops):
        from_op = OPERATORS[idx]
        assert from_op is not to_op


def test_build_mutations_returns_valid_indices():
    for idx, _to_op in build_mutations(OPERATORS, to_ops):
        assert idx < len(OPERATORS)


def test_build_mutations_produces_valid_pairs():
    for idx, to_op in build_mutations(OPERATORS, to_ops):
        from_op = OPERATORS[idx]
        assert from_op in OPERATORS
        assert to_op in OPERATORS or to_op is None
