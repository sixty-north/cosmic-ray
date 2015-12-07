"""Facilities for generating ASTs from modules.
"""

import ast
import logging

LOG = logging.getLogger()

# TODO: This is where we can do different things for different kinds of
# modules. Right now we only really handle normal source-code, text-file
# modules.


def get_ast(module):
    """Generate an AST from a module object.

    This will be the AST for the contents of the module.
    """
    with open(module.__file__, 'rt', encoding='utf-8') as module_file:
            LOG.info('reading module %s from %s',
                     module.__name__,
                     module.__file__)
            source = module_file.read()

    return ast.parse(source, module.__file__, 'exec')
