import cosmic_ray.tasks.worker
from .execution_engine import ExecutionEngine


class LocalExecutionEngine(ExecutionEngine):
    def __call__(self, timeout, pending_work, config):
        for work_record in pending_work:
            yield cosmic_ray.tasks.worker.worker_task(
                work_record,
                timeout,
                config)
