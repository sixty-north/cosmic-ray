# A set of function which exercise specific mutation operators. This
# is paired up with a test suite. The idea is that cosmic-ray should
# kill every mutant when that suite is run; if it doesn't, then we've
# got a problem.

import ctypes
import functools
import operator

# Add mutation points for comparison operators.

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

    raise Exception('bool_if() failed')


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

    return all([constraint(x, y)
                for x in vals
                for y in vals])


def use_break(limit):
    for x in range(limit):
        break
    return x


def use_continue(limit):
    for x in range(limit):
        continue
    return x


def trigger_infinite_loop():
    result = None
    # When `break` becomes `continue`, this should enter an infinite loop. This
    # helps us test timeouts.
    # Any object which isn't None passes the truth value testing so here
    # we use `while object()` instead of `while True` b/c the later becomes
    # `while False` when ReplaceTrueFalse is applied and we don't trigger an
    # infinite loop.
    while object():
        result = object()
        break

    # when `while object()` becomes `while not object()`
    # the code below will be triggered
    return result


def single_iteration():
    result = None
    iter = [object()]

    for i in iter:
        result = True

    return result


def handle_exception():
    result = None
    try:
        raise IOError
    except IOError:
        result = True

    return result


def decorator(func):
    func.cosmic_ray = True
    return func


@decorator
def decorated_func():
    result = None
    if decorated_func.cosmic_ray:
        result = True

    return result


def use_ctypes(size):
    array_type = ctypes.c_char * size

    chars_a = array_type(*(b'a' * size))
    chars_b = array_type(*(b'b' * size))

    # This odd construct ensures that, under number mutation to increase number
    # values, `size` varies by amounts big enough to trigger a segfault on the
    # sbsequent memmove.
    size = functools.reduce(operator.mul, [10, 10, 10, 10, 10, 10])
    ctypes.memmove(chars_a, chars_b, size)
    return chars_a.value


# This exists to give us some code to "skip" with spor anchors.
if __name__ == '__main__':
    x = 3
