"""adam.adam_1
"""

# pylint: disable=C0111
import operator

from math import *  # noqa: F401,F403

# Add mutation points for comparison operators.

def _(x): return x


def constant_number():
    return 42


def constant_true():
    return True


def constant_false():
    return False


def bool_and():
    return object() and None


def bool_or():
    return object() or None


def bool_expr_with_not():
    return not object()


def bool_if():
    if object():
        return True

    raise Exception(_("bool_if() failed"))


def if_expression():
    return True if object() else None


def assert_in_func():
    assert object()
    return True


def unary_sub():
    return -1


def unary_add():
    return +1


def binary_add():
    return 5 + 6


def equals(vals):
    def constraint(x, y):
        return operator.xor(x == y, x != y)

    return all([constraint(x, y) for x in vals for y in vals])


def use_break(limit):
    for x in range(limit):
        break
    return x


def use_continue(limit):
    for x in range(limit):
        continue
    return x


def use_star_args(*args):
    pass


def use_extended_call_syntax(x):
    use_star_args(*x)


def use_star_expr(x):
    a, *b = x
