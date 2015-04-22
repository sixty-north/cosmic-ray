import logging
import multiprocessing
import re
import sys

from stevedore import driver, extension

from cosmic_ray.config import load_configuration
from cosmic_ray.find_modules import find_modules
from cosmic_ray.mutating import create_mutants, run_with_mutant
import cosmic_ray.operators
from cosmic_ray.testing.test_runner import TestResult, Outcome


LOG = logging.getLogger()


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

        LOG.info('all tests initiated')

        for rec, async_result in test_results:
            try:
                # TODO: This timeout needs to be configurable.
                result = async_result.get(timeout=timeout)
            except multiprocessing.TimeoutError:
                result = TestResult(Outcome.INCOMPETENT, 'timeout')

            LOG.info('mutation record: %s', rec)
            LOG.info('result: %s', result)

            yield (rec, result)


def filtered_modules(modules, excludes):
    exclude_patterns = [re.compile(ex) for ex in excludes]
    for module in modules:
        if not any([pattern.match(module.__name__)
                    for pattern in exclude_patterns]):
            yield module


def main():
    configuration = load_configuration()

    if configuration['--verbose']:
        logging.basicConfig(level=logging.INFO)

    timeout = float(configuration['--timeout'])

    if not configuration['--no-local-import']:
        sys.path.insert(0, '')

    modules = filtered_modules(
        find_modules(configuration['<top-module>']),
        configuration['--exclude-modules'])

    # We don't use the extensions directly. This just forces importing
    # of modules which contain operators.
    extension.ExtensionManager(
        namespace='cosmic_ray.operators')

    operators = cosmic_ray.operators.all_operators()

    test_runner = driver.DriverManager(
        namespace='cosmic_ray.test_runners',
        name=configuration['--test-runner'],
        invoke_on_load=True,
        invoke_args=(configuration['<test-dir>'],),
    ).driver

    results = hunt(
        mutation_records=create_mutants(modules, operators),
        test_runner=test_runner,
        timeout=timeout)

    outcomes = {o: 0 for o in Outcome}

    for mutation_record, test_result in results:
        outcomes[test_result.outcome] += 1
        print(format_test_result(mutation_record, test_result))  # pylint:disable=superfluous-parens

    total_count = sum(outcomes.values())

    if total_count > 0:
        print('Survival rate: {:0.2f}%'.format(
            100 * outcomes[Outcome.SURVIVED] / total_count))
    else:
        print('No tests run (no mutations generated).')  # pylint:disable=superfluous-parens

    sys.exit(0 if outcomes[Outcome.SURVIVED] == 0 else 1)

if __name__ == '__main__':
    main()
