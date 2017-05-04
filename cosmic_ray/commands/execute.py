import cosmic_ray.tasks.celery
import cosmic_ray.tasks.worker
from cosmic_ray.work_record import WorkRecord

# TODO: These should be put into plugins. Callers of execute() should pass an
# executor.


def local_executor(test_runner, test_args, timeout, pending_work):
    for work_record in pending_work:
        yield cosmic_ray.tasks.worker.worker_task(
            work_record,
            test_runner,
            test_args,
            timeout)


class CeleryExecutor:
    def __init__(self, purge_queue=True):
        self.purge_queue = purge_queue

    def __call__(self, test_runner, test_args, timeout, pending_work):
        try:
            results = cosmic_ray.tasks.worker.execute_work_records(
                test_runner,
                test_args,
                timeout,
                pending_work)

            for r in results:
                yield WorkRecord(r.get())
        finally:
            if self.purge_queue:
                cosmic_ray.tasks.celery.app.control.purge()


def execute(work_db, dist=True):
    """Execute any pending work in `work_db`, recording the results.

    This looks for any work in `work_db` which has no results, schedules to be
    executed, and records any results that arrive.

    If `dist` is `True` then this uses Celery to distribute tasks to remote
    workers; of course you need to make sure that these are running if you want
    tests to actually run! If `dist` is `False` then all tests will be run
    locally.
    """
    test_runner, test_args, timeout = work_db.get_work_parameters()
    executor = CeleryExecutor() if dist else local_executor
    work_records = executor(test_runner,
                            test_args,
                            timeout,
                            work_db.pending_work)
    for work_record in work_records:
        work_db.update_work_record(work_record)
