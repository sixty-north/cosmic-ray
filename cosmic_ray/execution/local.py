from .execution_engine import ExecutionEngine
from ..worker import worker_process


# pylint: disable=too-few-public-methods
class LocalExecutionEngine(ExecutionEngine):
    def __call__(self, timeout, pending_work, config):
        for work_record in pending_work:
            yield worker_process(work_record, timeout, config)
