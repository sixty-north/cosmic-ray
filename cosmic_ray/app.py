"""cosmic-ray

Usage:
  cosmic-ray [options] <module> <test-dir>

Options:
  -h --help          Show this screen.
  --verbose          Produce verbose output
  --no-local-import  Allow importing module from the current directory
"""
import functools
import logging
import multiprocessing
import sys

import docopt

import cosmic_ray.find_modules
from cosmic_ray.mutating import create_mutants, run_with_mutant
import cosmic_ray.operators
from cosmic_ray.testing import Outcome, run_tests


log = logging.getLogger()


def format_test_result(mutation_record, test_result):
    """Returns a reasonably formatted string with test outcome,
    activation-record information, and reason.
    """
    arec = mutation_record.activation_record

    return '{outcome} -> {desc} @ {filename}:{lineno}\n{reason}'.format(
        outcome=test_result.outcome,
        desc=arec['description'],
        filename=mutation_record.module_file,
        lineno=arec['line_number'],
        reason=test_result.results)


def _test_func(test_func, mutation_record):
    return (mutation_record,
            run_with_mutant(test_func,
                            mutation_record))


def hunt(mutation_records, test_function):
    """Call `test_function` for each mutant in `mutation_records`.

    Returns a sequence of (MutationRecord, TestResult) tuples.
    """

    with multiprocessing.Pool() as p:
        yield from p.map(
            functools.partial(_test_func, test_function),
            mutation_records)


def main():
    arguments = docopt.docopt(__doc__, version='cosmic-ray v.2')
    if arguments['--verbose']:
        logging.basicConfig(level=logging.INFO)

    if not arguments['--no-local-import']:
        sys.path.insert(0, '')

    modules = cosmic_ray.find_modules.find_modules(arguments['<module>'])

    operators = cosmic_ray.operators.all_operators()

    test_function = functools.partial(run_tests,
                                      arguments['<test-dir>'])

    results = hunt(
        create_mutants(modules, operators),
        test_function)

    outcomes = {o: 0 for o in Outcome}

    for mutation_record, test_result in results:
        outcomes[test_result.outcome] += 1
        print(format_test_result(mutation_record, test_result))

    total_count = sum(outcomes.values())
    print('Survival rate: {:0.2f}%'.format(
        100 * outcomes[Outcome.SURVIVED] / total_count))

if __name__ == '__main__':
    main()
