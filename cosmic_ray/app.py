"""cosmic-ray

Usage:
  cosmic-ray [options] <module> <test-dir>

Options:
  -h --help         Show this screen.
  --timeout=<t>     Maximum time (seconds) a mutant may run [default: 5]
  --verbose         Produce verbose output
  --no-local-import Allow importing module from the current directory
"""

import logging
import multiprocessing
import sys

import docopt

import cosmic_ray.find_modules
from cosmic_ray.mutating import create_mutants, run_with_mutant
import cosmic_ray.operators
from cosmic_ray.testing import TestResult, Outcome, UnittestRunner


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


def hunt(mutation_records, test_runner, timeout):
    """Call `test_runner` for each mutant in `mutation_records`.

    `test_runner` should be a `TestRunner` instance.

    Returns a sequence of `(MutationRecord, TestResult)` tuples.
    """

    with multiprocessing.Pool(maxtasksperchild=1) as pool:
        test_results = ((rec,
                         pool.apply_async(run_with_mutant,
                                          args=(test_runner, rec)))
                        for rec in mutation_records)

        logging.info('all tests initiated')

        for rec, async_result in test_results:
            try:
                # TODO: This timeout needs to be configurable.
                result = async_result.get(timeout=timeout)
            except multiprocessing.TimeoutError:
                result = TestResult(Outcome.INCOMPETENT, 'timeout')

            logging.info('mutation record: {}'.format(rec))
            logging.info('result: {}'.format(result))

            yield (rec, result)


def main():
    arguments = docopt.docopt(__doc__, version='cosmic-ray v.2')

    if arguments['--verbose']:
        logging.basicConfig(level=logging.INFO)

    timeout = float(arguments['--timeout'])

    if not arguments['--no-local-import']:
        sys.path.insert(0, '')

    modules = cosmic_ray.find_modules.find_modules(arguments['<module>'])

    operators = cosmic_ray.operators.all_operators()

    test_runner = UnittestRunner(arguments['<test-dir>'])

    results = hunt(
        mutation_records=create_mutants(modules, operators),
        test_runner=test_runner,
        timeout=timeout)

    outcomes = {o: 0 for o in Outcome}

    for mutation_record, test_result in results:
        outcomes[test_result.outcome] += 1
        print(format_test_result(mutation_record, test_result))

    total_count = sum(outcomes.values())
    print('Survival rate: {:0.2f}%'.format(
        100 * outcomes[Outcome.SURVIVED] / total_count))

if __name__ == '__main__':
    main()
