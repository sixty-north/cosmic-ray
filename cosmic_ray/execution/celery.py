import cosmic_ray.tasks.worker
from cosmic_ray.work_record import WorkRecord
from .execution_engine import ExecutionEngine


# pylint: disable=too-few-public-methods
class CeleryExecutionEngine(ExecutionEngine):
    def __call__(self, timeout, pending_work, config):
        # TODO: Configure purge-queue via the config.
        purge_queue = True

        try:
            results = cosmic_ray.tasks.worker.execute_work_records(
                timeout,
                pending_work,
                config)

            for result in results:
                yield WorkRecord(result.get())
        finally:
            if purge_queue:
                cosmic_ray.tasks.celery.app.control.purge()
