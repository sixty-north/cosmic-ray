"""Celery specific details for routing work requests to Cosmic Ray workers."""
import celery
import celery.signals
from celery.utils.log import get_logger

from cosmic_ray.worker import worker
from cosmic_ray.work_item import WorkItem

from .app import APP

LOG = get_logger(__name__)


@APP.task(name="cosmic_ray_celery4_engine.worker")
def worker_task(work_item, timeout, config):
    """The celery task which performs a single mutation and runs a test suite.

    This runs `cosmic-ray worker` in a subprocess and returns the results,
    passing `config` to it via stdin.

    Args:
        work_item: A dict describing a WorkItem.
        timeout: The max length of time to let a test run before it's killed
        config: The configuration to use for the test execution.

    Returns: An updated WorkItem
    """
    result = worker(
        work_item.module_path,
        config.python_version,
        work_item.operator_name,
        work_item.occurrence,
        config["test-command"],
        timeout,
    )
    return work_item.job_id, result


def execute_work_items(timeout, work_items, config):
    """Execute a suite of tests for a given set of work items.

    Args:
      timeout: The max length of time to let a test run before it's killed.
      work_items: An iterable of `work_db.WorkItem`s.
      config: The configuration to use for the test execution.

    Returns: An iterable of WorkItems.
    """
    return celery.group(
        worker_task.s(work_item, timeout, config) 
        for work_item in work_items
    )


def foo(*args, **kwargs):
    print("worker_process_init", args, kwargs)


celery.signals.worker_process_init.connect(foo)