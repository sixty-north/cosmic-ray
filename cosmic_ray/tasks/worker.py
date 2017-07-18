"""Celery specific details for routing work requests to Cosmic Ray workers."""
import celery
from celery.utils.log import get_logger
import itertools
import json
import subprocess

from .celery import app
from ..worker import WorkerOutcome
from ..work_record import WorkRecord

LOG = get_logger(__name__)


@app.task(name='cosmic_ray.tasks.worker')
def worker_task(work_record,
                test_runner,
                test_args,
                timeout):
    """The celery task which performs a single mutation and runs a test suite.

    This runs `cosmic-ray worker` in a subprocess and returns the results.

    Returns: An updated WorkRecord
    """
    # The work_record param may come as just a dict (e.g. if it arrives over
    # celery), so we reconstruct a WorkRecord to make it easier to work with.
    work_record = WorkRecord(work_record)

    command = list(itertools.chain(
        ('cosmic-ray',
         'worker',
         work_record.module,
         work_record.operator,
         str(work_record.occurrence),
         test_runner,
         '--',),
        test_args))

    LOG.info('executing: %s', command)

    proc = subprocess.Popen(command,
                            stdout=subprocess.PIPE,
                            universal_newlines=True)
    try:
        outs, _ = proc.communicate(input=None, timeout=timeout)
        result = json.loads(outs)
        work_record.update({
            k: v
            for k, v
            in result.items()
            if v is not None
        })
    except subprocess.TimeoutExpired as e:
        work_record.worker_outcome = WorkerOutcome.TIMEOUT
        work_record.data = e.timeout
        proc.kill()
    except json.JSONDecodeError as e:
        work_record.worker_outcome = WorkerOutcome.EXCEPTION
        work_record.data = e

    work_record.command_line = command
    return work_record


def execute_work_records(test_runner,
                         test_args,
                         timeout,
                         work_records):
    """Execute a suite of tests for a given set of work items.

    Args:
      test_runner: The `TestRunner` instance to use for running tests.
      test_args: The list of arguments to pass to the test runner.
      timeout: The max length of time to let a test run before it's killed.
      work_records: An iterable of `work_db.WorkItem`s.

    Returns: An iterable of WorkRecords.
    """
    return celery.group(
        worker_task.delay(work_record,
                          test_runner,
                          test_args,
                          timeout)
        for work_record in work_records)
