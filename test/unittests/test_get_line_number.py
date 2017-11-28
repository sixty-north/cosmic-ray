import ast

from cosmic_ray.util import get_line_number


def test_basic():
    code = 'if x == 1:' \
           '    return 3'
    tree = ast.parse(code)

    assert get_line_number(tree) == -1
    assert get_line_number(tree.body[0]) == 1
    assert get_line_number(tree.body[0].test) == 1
    assert get_line_number(tree.body[0].test.ops[0]) == -1
