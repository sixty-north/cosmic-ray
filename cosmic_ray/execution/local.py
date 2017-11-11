"Implementation of the local execution engine."

from .execution_engine import ExecutionEngine
from ..worker import worker_process


class LocalExecutionEngine(ExecutionEngine):
    "Execution engine that runs jobs on the local machine."
    def __call__(self, timeout, pending_work_items, config):
        for work_item in pending_work_items:
            yield worker_process(work_item, timeout, config)
