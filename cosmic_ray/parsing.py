"""Facilities for generating ASTs from modules."""

import ast
import inspect
import logging

log = logging.getLogger()


# This is where we can do different things for different kinds of modules.
# Right now we only really handle normal source-code, text-file modules.


def get_ast(module):
    """Generate an AST from a module object.

    This will be the AST for the contents of the module.

    Raises:
        OSError: If the source code for `module` can't be found.
        TypeError: If the source file for `module` can't be found.
    """
    try:
        source_file = inspect.getsourcefile(module)
    except TypeError:
        log.error("Unable to get source file for object %s", module)
        raise

    try:
        source = inspect.getsource(module)
    except OSError:
        # workaround for empty __init__.py files, see
        # http://bugs.python.org/issue27578
        if source_file.endswith('__init__.py'):
            source = ''
        else:
            log.info('inspect.getsource() failed.'
                     'Attempting to read source directly: %s',
                     module)
            with open(source_file, mode='rt') as handle:
                source = handle.read()

    return ast.parse(source, source_file, 'exec')
