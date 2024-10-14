"""adam.adam_2"""


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
    iterable = [object()]

    for i in iterable:  # pylint: disable=W0612
        result = True

    return result


def handle_exception():
    result = None
    try:
        raise OSError
    except OSError:
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
