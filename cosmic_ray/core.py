import asyncio
import logging
import multiprocessing
import sys

import pykka

from cosmic_ray.mutating import run_with_mutant
from cosmic_ray.testing.test_runner import Outcome, TestResult

LOG = logging.getLogger()


def _format_test_result(mutation_record, test_result):
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
        print(_format_test_result(mutation_record, test_result),
              file=self._file_like)


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


def test_mutants(mutation_records,
                 test_runner,
                 num_testers,
                 timeout,
                 *handlers):
    LOG.info('Using {} concurrent testers'.format(num_testers))
    LOG.info('Creating actors')

    queue = QueueManager.start(mutation_records).proxy()
    logger = Logger.start().proxy()
    testers = [MutantTester.start(test_runner, timeout, logger, *handlers)
               for _ in range(num_testers)]

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
            LOG.info('stopping loop...')
            loop.stop()

    # Schedule a call to check_testers
    loop.call_soon(check_testers)

    LOG.info('scheduled test checking')

    LOG.info('Starting event loop')
    loop.run_forever()
    LOG.info('Closing the event loop')
    loop.close()
    LOG.info('Event loop closed')

    LOG.info('Stopping actors')
    queue.stop()
    logger.stop()
    LOG.info('Actors stopped')
