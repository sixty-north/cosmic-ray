import sys

import decorator


@decorator.decorator
def isolate_import_environment(f, *args, **kwargs):
    """A decorator which ensures that `sys.meta_path` and `sys.modules`
    are restored to their initial state after the call.

    This helps ensure a stable environment for performing operations
    that might add finders and/or import modules that we want to
    reimport.
    """
    meta_path = sys.meta_path[:]
    modules = dict(sys.modules)

    try:
        return f(*args, **kwargs)
    finally:
        sys.meta_path = meta_path
        sys.modules = modules


def get_line_number(node):
    if hasattr(node, 'lineno'):
        return node.lineno
    else:
        return '<UNKNOWN>'
