# Find all of the modules that need to be mutated
# Create ASTs for all of the modules
# Foreach AST:
#    foreach operation:
#        foreach location in AST where op applies:
#            apply op to location
#            Make that AST active/replace old module with new
#            run all tests
#            If not failures, mutant survived!

import logging
import sys
import unittest

from .importing import install_finder
from .operators import all_operators
from .util import isolate_import_environment

log = logging.getLogger()

SURVIVED = 'survived'
KILLED = 'killed'
INCOMPETENT = 'incompetent'


@isolate_import_environment
def run_tests(test_dir):
    """Discover and run all tests in `test_dir`.
    """
    try:
        suite = unittest.TestLoader().discover(test_dir)
        result = unittest.TestResult()
        suite.run(result)
        if result.wasSuccessful:
            return SURVIVED
        else:
            return KILLED
    except Exception:
        return INCOMPETENT


def mutation_testing(finder, test_dir):
    def test(module_name, mutant):
        finder[module_name] = mutant
        sys.modules.pop(module_name, None)
        return run_tests(test_dir)

    return [(record, test(module_name, mutant))
            for module_name, ast_node in finder.items()
            for operator in all_operators()
            for record, mutant in operator.bombard(ast_node)]


if __name__ == '__main__':
    with install_finder(sys.argv[1]) as finder:
        results = mutation_testing(finder, sys.argv[2])

    import pprint
    pprint.pprint(results)
