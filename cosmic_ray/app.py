import ast
from functools import partial
import logging
import multiprocessing
import sys
import types
import unittest

from cosmic_ray.find_modules import find_modules
from cosmic_ray.operators import all_operators

log = logging.getLogger()

SURVIVED = 'survived'
KILLED = 'killed'
INCOMPETENT = 'incompetent'


def run_with_mutants(module_file, module_name, operator, func, q):
    """Run a function for each mutatation of a module.

    Mutate the module specified by `module_file` and `module_name`
    using `operator`. For each mutation, install that mutant into the
    module registry and then run `func`, putting `func`'s return value
    into the queue `q`.

    If `func` raises an exception, then a tuple (INCOMPETENT,
    exception-info) is placed into `q`.

    This is designed to be run in its own process, specifically via
    the `multiprocessing` module.
    """
    with open(module_file, 'rt') as f:
        log.info('reading module {} from {}'.format(
            module_name, module_file))
        source = f.read()

    log.info('parsing module {}'.format(module_name))

    pristine_ast = ast.parse(source, module_file, 'exec')

    log.info('{} successfully parsed'.format(module_name))

    for record, mutant in operator.bombard(pristine_ast):
        try:
            new_mod = types.ModuleType(module_name)
            code = compile(mutant, module_file, 'exec')
            sys.modules[module_name] = new_mod
            exec(code,  new_mod.__dict__)
            q.put(func())
        except Exception as e:
            q.put((INCOMPETENT, str(e)))


def run_test(test_dir):
    """Discover and run tests in `test_dir`.

    If the tests pass, this returns `(SURVIVED, result)`, otherwise it
    returns `(KILLED, result)`.
    """
    suite = unittest.TestLoader().discover(test_dir)
    result = unittest.TestResult()
    suite.run(result)
    if result.wasSuccessful():
        return SURVIVED, str(result)
    else:
        return KILLED, str(result)


def main(top_module, test_dir):
    """Runs the tests in `test_dir` against mutated version of
    `top_module`.

    This finds all of the modules in and including `top_module`. For
    each of these modules, it mutates them using all of the available
    mutation operators. For each mutant, the tests in `test_dir` are
    executed. The result of a bunch of records telling us whether the
    mutant survived, was killed, or was incompetent.
    """
    modules = list(find_modules(top_module))

    # Remove those names from sys.modules. Tests will import them on
    # their own after mutation.
    # TODO: This doesn't seem necessary now.
    for m in modules:
        del sys.modules[m.__name__]

    test_runner = partial(run_test, test_dir)

    mp_mgr = multiprocessing.Manager()
    response_queue = mp_mgr.Queue()

    with multiprocessing.Pool() as p:
        p.starmap(
            run_with_mutants,
            [(m.__file__, m.__name__, op, test_runner, response_queue)
             for m in modules
             for op in all_operators()])

    while not response_queue.empty():
        print(response_queue.get())

if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    main(sys.argv[1], sys.argv[2])
