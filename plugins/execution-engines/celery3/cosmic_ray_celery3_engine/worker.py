"""Celery specific details for routing work requests to Cosmic Ray workers."""
import celery
from celery.utils.log import get_logger

from cosmic_ray.worker import worker_process

from .app import APP

LOG = get_logger(__name__)


@APP.task(name='cosmic_ray_celery3_engine.worker')
def worker_task(work_item,
                timeout,
                config):
    """The celery task which performs a single mutation and runs a test suite.

    This runs `cosmic-ray worker` in a subprocess and returns the results,
    passing `config` to it via stdin.

    Returns: An updated WorkItem

    """
    return worker_process(work_item, timeout, config)


def execute_work_items(timeout,
                       work_items,
                       config):
    """Execute a suite of tests for a given set of work items.

    Args:
      timeout: The max length of time to let a test run before it's killed.
      work_items: An iterable of `work_db.WorkItem`s.
      config: The configuration to use for the test execution.

    Returns: An iterable of WorkItems.
    """
    return celery.group(
        worker_task.delay(work_item,
                          timeout,
                          config)
        for work_item in work_items)
