"""Celery specific details for routing work requests to Cosmic Ray workers."""
import os

import celery
from celery.utils.log import get_logger
from cosmic_ray.cloning import ClonedWorkspace
from cosmic_ray.worker import worker

from .app import APP

log = get_logger(__name__)

# TODO: This is a bit incorrect. We need some notion of a workspace
# per config, or at least a workspace per source clone. In principle, at least,
# a worker could be asked to do work for more than one workspace. Perhaps the best
# thing to do is have the worker refuse the work.
_workspace = None

# This is just for ensuring that I know what I'm doing. We can remove
# this later.
_pid = None


@APP.task(name="cosmic_ray_celery4_engine.worker")
def worker_task(work_item, config):
    """The celery task which performs a single mutation and runs a test suite.

    This runs `cosmic-ray worker` in a subprocess and returns the results,
    passing `config` to it via stdin.

    Args:
        work_item: A dict describing a WorkItem.
        config: The configuration to use for the test execution.

    Returns: An updated WorkItem
    """
    global _workspace

    _ensure_workspace(config)

    result = worker(
        work_item.module_path,
        config.python_version,
        work_item.operator_name,
        work_item.occurrence,
        config.test_command,
        config.timeout)
    return work_item.job_id, result


def _ensure_workspace(config):
    global _workspace
    global _pid

    if _workspace is not None:
        assert _pid == os.getpid()
        return

    log.info('Initialize celery4 workspace in PID %s', os.getpid())
    _workspace = ClonedWorkspace(config.cloning_config)
    _pid = os.getpid()

    os.chdir(_workspace.clone_dir)


def execute_work_items(work_items, config):
    """Execute a suite of tests for a given set of work items.

    Args:
      work_items: An iterable of `work_db.WorkItem`s.
      config: The configuration to use for the test execution.

    Returns: An iterable of WorkItems.
    """
    return celery.group(
        worker_task.s(work_item, config)
        for work_item in work_items
    )
