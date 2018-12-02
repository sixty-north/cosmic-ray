"Implementation of the local execution engine."

from .execution_engine import ExecutionEngine
from ..worker import worker


class LocalExecutionEngine(ExecutionEngine):
    "Execution engine that runs jobs on the local machine."

    def __call__(self, timeout, pending_work_items, config, on_task_complete):
        for work_item in pending_work_items:
            work_result = worker(
                work_item.module_path,
                config.python_version,
                work_item.operator_name,
                work_item.occurrence,
                config["test-command"],
                timeout,
            )

            on_task_complete(work_item.job_id, work_result)
