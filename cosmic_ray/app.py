import asyncio
import logging
import multiprocessing
import re
import sys

import pykka
from stevedore import driver, extension, ExtensionManager

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
        desc=arec.get('description', '<NO DESCRIPTION>'),
        filename=mutation_record.module_file,
        lineno=arec.get('line_number', '<NO LINE NUMBER>'),
        reason=test_result.results)


class QueueManager(pykka.ThreadingActor):
    """An actor that distributes the mutation records to testers.
    """
    def __init__(self, mutation_records):
        super().__init__()  # pylint:disable=missing-super-argument
        self._record_iterator = iter(mutation_records)

    def next(self):
        """Return the next mutation record, or `None` if there are no more
        records.
        """
        try:
            return next(self._record_iterator)
        except StopIteration:
            return None


class Logger(pykka.ThreadingActor):
    """A simple logging actor.

    This received test results and just writes them to the console.
    """
    def __init__(self, file_like=sys.stdout):
        super().__init__()  # pylint:disable=missing-super-argument
        self._file_like = file_like

    def handle_result(self, mutation_record, test_result):
        print(format_test_result(mutation_record, test_result),
              file=self._file_like)


class Summarizer(pykka.ThreadingActor):
    """An actor that maintains simple statistics on the testing outcomes.
    """
    def __init__(self):
        super().__init__()  # pylint:disable=missing-super-argument
        self.outcomes = {o: 0 for o in Outcome}

    def handle_result(self, mutation_record, test_result):
        self.outcomes[test_result.outcome] += 1


class MutantTester(pykka.ThreadingActor):
    """An actor that executes tests on mutants.
    """
    def __init__(self, test_runner, timeout, *handlers):
        super().__init__()  # pylint:disable=missing-super-argument
        self._test_runner = test_runner
        self._timeout = timeout
        self._handlers = handlers
        self._pool = multiprocessing.Pool(maxtasksperchild=1)

    def on_stop(self):
        self._pool.terminate()

    def on_receive(self, msg):
        if 'process_queue' in msg:
            self._process_queue(msg['process_queue'])

    def _process_queue(self, queue):
        """Fetch the next mutation records from the queue and test it.

        If there are no more records, this calls
        `self.stop`. Otherwise, after testing the mutant, this sends a
        message to itself to process another mutant.
        """
        record = queue.next().get()

        if record is None:
            self.stop()
            return

        future = self._pool.apply_async(
            run_with_mutant,
            (self._test_runner, record))

        try:
            result = future.get(timeout=self._timeout)
        except multiprocessing.TimeoutError:
            result = TestResult(Outcome.INCOMPETENT, 'timeout')

        for h in self._handlers:
            h.handle_result(record, result)

        self.actor_ref.tell({'process_queue': queue})


def filtered_modules(modules, excludes):
    """Get the sequence of modules in `modules` which aren't filtered out
    by a regex in `excludes`.

    """
    exclude_patterns = [re.compile(ex) for ex in excludes]
    for module in modules:
        if not any([pattern.match(module.__name__)
                    for pattern in exclude_patterns]):
            yield module


def get_test_runner(configuration):
    """Get the test-runner instance specified in the configuration.

    This also checks to see if the user has requested a list of
    test-runners. If so, this prints the runners and exits the
    program.
    """
    if configuration['test-runners']:
        for name in ExtensionManager('cosmic_ray.test_runners').names():
            print(name)
        sys.exit(0)

    test_runner_manager = driver.DriverManager(
        namespace='cosmic_ray.test_runners',
        name=configuration['--test-runner'],
        invoke_on_load=True,
        invoke_args=(configuration['<test-dir>'],),
    )

    return test_runner_manager.driver


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
    test_runner = get_test_runner(configuration)

    mutation_records = create_mutants(modules, operators)

    LOG.info('Creating actors')

    queue = QueueManager.start(mutation_records).proxy()
    logger = Logger.start().proxy()
    summarizer = Summarizer.start().proxy()
    testers = [MutantTester.start(test_runner, timeout, logger, summarizer)
               for _ in range(4)]  # TODO: Configurable!

    LOG.info('Created actors')

    for tester in testers:
        tester.tell({'process_queue': queue})

    LOG.info('started tester processing')

    loop = asyncio.get_event_loop()

    LOG.info('created event loop')

    def check_testers():
        """Check to see if any testers are still alive, terminating the event
        loop if not.
        """
        if any([t.is_alive() for t in testers]):
            loop.call_soon(check_testers)
        else:
            LOG.info('stopping loopg...')
            loop.stop()

    # Schedule a call to check_testers
    loop.call_soon(check_testers)

    LOG.info('scheduled test checking')

    LOG.info('Starting event loop')
    loop.run_forever()
    LOG.info('Closing the event loop')
    loop.close()
    LOG.info('Event loop closed')

    outcomes = summarizer.outcomes.get()

    LOG.info('Stopping actors')
    queue.stop()
    logger.stop()
    summarizer.stop()
    LOG.info('Actors stopped')

    total_count = sum(outcomes.values())

    if total_count > 0:
        print('Survival rate: {:0.2f}%'.format(
            100 * outcomes[Outcome.SURVIVED] / total_count))
    else:
        print('No tests run (no mutations generated).')  # pylint:disable=superfluous-parens

    sys.exit(0 if outcomes[Outcome.SURVIVED] == 0 else 1)

if __name__ == '__main__':
    main()
