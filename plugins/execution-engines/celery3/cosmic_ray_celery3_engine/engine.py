"Implementation of the celery3 execution engine plugin."

from cosmic_ray.execution.execution_engine import ExecutionEngine
from cosmic_ray.work_item import WorkItem

from .app import APP
from .worker import execute_work_items


class CeleryExecutionEngine(ExecutionEngine):
    "The celery3 execution engine."
    def __call__(self, timeout, pending_work, config, on_task_complete):
        purge_queue = config['execution-engine'].get('purge-queue', True)

        # def on_task_complete(*args, **kwargs):
        #     print("on_task_complete")
        #     print("  args   =", args)
        #     print("  kwargs =", kwargs)
        #     print()

        try:
            job = execute_work_items(
                timeout,
                pending_work,
                config)

            result = job.apply_async()
            print("Waiting!")
            result.get(callback=on_task_complete)
            print("All done!")
        finally:
            if purge_queue:
                APP.control.purge()
