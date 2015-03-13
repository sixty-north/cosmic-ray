"""cosmic-ray

Usage:
  cosmic-ray [options] <module> <test-dir>

Options:
  -h --help     Show this screen.
  --verbose     Produce verbose output
"""
import logging
import multiprocessing
import sys
from functools import partial

import docopt

from cosmic_ray.find_modules import find_modules
from cosmic_ray.mutating import run_with_mutants
from cosmic_ray.operators import all_operators
from cosmic_ray.testing import run_tests

log = logging.getLogger()


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

    test_runner = partial(run_tests, test_dir)

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
    arguments = docopt.docopt(__doc__, version='cosmic-ray v.1')
    if arguments['--verbose']:
        logging.basicConfig(level=logging.INFO)

    main(arguments['<module>'],
         arguments['<test-dir>'])
