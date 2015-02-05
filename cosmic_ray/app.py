# Find all of the modules that need to be mutated
# Create ASTs for all of the modules
# Foreach AST:
#    foreach operation:
#        foreach location in AST where op applies:
#            apply op to location
#            Make that AST active/replace old module with new
#            run all tests
#            If not failures, mutant survived!

import ast
import logging
import sys
import unittest

import decorator

from .find_modules import find_modules
from .importing import Finder
from .operations import delete_arithmetic_operators, replace_constants

log = logging.getLogger()


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


@isolate_import_environment
def create_finder(module_name):
    finder = Finder()

    for module in find_modules(module_name):
        with open(module.__file__, 'rt') as f:
            log.info('Reading module {} from {}'.format(
                module.__name__, module.__file__))
            source = f.read()

        log.info('Parsing module {}'.format(module.__name__))

        finder[module.__name__] = ast.parse(
            source, module.__file__, 'exec')

    return finder


@isolate_import_environment
def run_tests(test_dir):
    try:
        suite = unittest.TestLoader().discover(test_dir)
        result = unittest.TestResult()
        suite.run(result)
        if result.wasSuccessful:
            log.info('survived: mutant')
        else:
            log.info('killer: mutant')
    except Exception:
        log.info('incompetent: mutant')


def mutation_testing(module_name, test_dir):
    finder = create_finder(module_name)

    sys.meta_path = [finder] + sys.meta_path

    operations = (replace_constants, delete_arithmetic_operators)
    for module_name, ast_node in finder.items():
        log.info('Mutating module {}'.format(module_name))

        pristine_ast = ast_node

        for operation in operations:
            log.info('Operation: {}'.format(operation))

            for idx, mutant in enumerate(operation(pristine_ast)):
                finder[module_name] = mutant

                sys.modules.pop(module_name, None)

                run_tests(test_dir)

        finder[module_name] = pristine_ast


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    mutation_testing(sys.argv[1], sys.argv[2])
