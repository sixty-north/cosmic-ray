"Implementation of the celery4 execution engine plugin."

from cosmic_ray.execution.execution_engine import ExecutionEngine

from .app import APP
from .worker import execute_work_items


class CeleryExecutionEngine(ExecutionEngine):
    "The celery4 execution engine."
    def __call__(self, timeout, pending_work, config, on_task_complete):
        purge_queue = config['execution-engine'].get('purge-queue', True)

        def celery_task_complete(task_id, result):
            on_task_complete(*result)

        try:
            job = execute_work_items(
                timeout,
                pending_work,
                config)

            result = job.apply_async()
            result.get(callback=celery_task_complete)
        finally:
            if purge_queue:
                APP.control.purge()
