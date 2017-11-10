"Implementation of the celery3 execution engine plugin."

from cosmic_ray.execution.execution_engine import ExecutionEngine
from cosmic_ray.work_item import WorkItem

from .app import APP
from .worker import execute_work_items


class CeleryExecutionEngine(ExecutionEngine):
    "The celery3 execution engine."
    def __call__(self, timeout, pending_work, config):
        purge_queue = config['execution-engine'].get('purge-queue', True)

        try:
            results = execute_work_items(
                timeout,
                pending_work,
                config)

            for result in results:
                yield WorkItem(result.get())
        finally:
            if purge_queue:
                APP.control.purge()
