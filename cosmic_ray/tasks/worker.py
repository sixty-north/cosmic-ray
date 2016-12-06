"""Celery specific details for routing work requests to Cosmic Ray workers."""
import itertools
import json
import subprocess
import celery

from .celery import app
from celery.utils.log import get_logger

LOG = get_logger(__name__)


@app.task(name='cosmic_ray.tasks.worker')
def worker_task(work_id,
                module,
                operator,
                occurrence,
                test_runner,
                test_args,
                timeout):
    """The celery task which performs a single mutation and runs a test suite.


    This runs `cosmic-ray worker` in a subprocess and returns the results.

    The results are a tuple `(work_id, command, results)` where `work_id` is
    the work_id passed into this function, `command` is the actual command
    executed by this worker in as a subprocess, and `results` is whatever is
    the JSON-decoded value printed by the worker subprocess.

    """
    command = list(itertools.chain(
        ('cosmic-ray',
         'worker',
         module,
         operator,
         str(occurrence),
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
    except subprocess.TimeoutExpired as e:
        result = ('timeout', e.timeout)
        proc.kill()
    return (work_id, command, result)


def execute_work_items(test_runner,
                       test_args,
                       timeout,
                       work_items):
    """Execute a suite of tests for a given set of work items.

    Args:
      test_runner: The `TestRunner` instance to use for running tests.
      test_args: The list of arguments to pass to the test runner.
      timeout: The max length of time to let a test run before it's killed.
      work_items: An iterable of `work_db.WorkItem`s.

    Returns: An iterable of `(work_id, command, results)` tuples as described
      in `worker_task()`.
    """
    return celery.group(
        worker_task.delay(work_item.work_id,
                          work_item.module_name,
                          work_item.operator_name,
                          work_item.occurrence,
                          test_runner,
                          test_args,
                          timeout)
        for work_item in work_items)
