import cosmic_ray.tasks.worker
from cosmic_ray.work_record import WorkRecord
from .execution_engine import ExecutionEngine


class CeleryExecutionEngine(ExecutionEngine):
    def __call__(self, timeout, pending_work, config):
        # TODO: Configure purge-queue via the config.
        purge_queue = True

        try:
            results = cosmic_ray.tasks.worker.execute_work_records(
                timeout,
                pending_work,
                config)

            for r in results:
                yield WorkRecord(r.get())
        finally:
            if purge_queue:
                cosmic_ray.tasks.celery.app.control.purge()
