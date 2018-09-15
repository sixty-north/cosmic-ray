"""Celery specific details for routing work requests to Cosmic Ray workers."""
import celery
from celery.utils.log import get_logger

from cosmic_ray.worker import execute_work_item
from cosmic_ray.work_item import WorkItem

from .app import APP

LOG = get_logger(__name__)


@APP.task(name='cosmic_ray_celery3_engine.worker')
def worker_task(work_item_dict,
                timeout,
                config):
    """The celery task which performs a single mutation and runs a test suite.

    This runs `cosmic-ray worker` in a subprocess and returns the results,
    passing `config` to it via stdin.

    Args:
        work_item: A dict describing a WorkItem.
        timeout: The max length of time to let a test run before it's killed
        config: The configuration to use for the test execution.

    Returns: An updated WorkItem
    """
    return execute_work_item(
        WorkItem(work_item_dict),
        timeout,
        config)


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
    print("execute_work_items")
    return celery.group(
        worker_task.s(work_item,
                      timeout,
                      config)
        for work_item in work_items)
