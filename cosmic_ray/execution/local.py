"Implementation of the local execution engine."

from .execution_engine import ExecutionEngine
from ..worker import worker_process


class LocalExecutionEngine(ExecutionEngine):
    "Execution engine that runs jobs on the local machine."
    def __call__(self, timeout, pending_work, config):
        for work_record in pending_work:
            yield worker_process(work_record, timeout, config)
