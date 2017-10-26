"""Celery specific details for routing work requests to Cosmic Ray workers."""
import celery
from celery.utils.log import get_logger
import json
import subprocess

import cosmic_ray.config
from .celery import app
from ..worker import WorkerOutcome
from ..work_record import WorkRecord

LOG = get_logger(__name__)


@app.task(name='cosmic_ray.tasks.worker')
def worker_task(work_record,
                timeout,
                config):
    """The celery task which performs a single mutation and runs a test suite.

    This runs `cosmic-ray worker` in a subprocess and returns the results,
    passing `config` to it via stdin.

    Returns: An updated WorkRecord

    """
    # The work_record param may come as just a dict (e.g. if it arrives over
    # celery), so we reconstruct a WorkRecord to make it easier to work with.
    work_record = WorkRecord(work_record)

    command = 'cosmic-ray worker {module} {operator} {occurrence}'.format(
        **work_record)

    LOG.info('executing: %s', command)

    proc = subprocess.Popen(command.split(),
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            universal_newlines=True)
    config_string = cosmic_ray.config.serialize_config(config)
    try:
        outs, _ = proc.communicate(input=config_string, timeout=timeout)
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


def execute_work_records(timeout,
                         work_records,
                         config):
    """Execute a suite of tests for a given set of work items.

    Args:
      timeout: The max length of time to let a test run before it's killed.
      work_records: An iterable of `work_db.WorkItem`s.
      config: The configuration to use for the test execution.

    Returns: An iterable of WorkRecords.
    """
    return celery.group(
        worker_task.delay(work_record,
                          timeout,
                          config)
        for work_record in work_records)
