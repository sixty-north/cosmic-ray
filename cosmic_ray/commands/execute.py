import cosmic_ray.tasks.celery
import cosmic_ray.tasks.worker

# TODO: These should be put into plugins. Callers of execute() should pass an
# executor.

def local_executor(test_runner, test_args, timeout, pending_work):
    for work_item in pending_work:
        result = cosmic_ray.tasks.worker.worker_task(
            work_item.work_id,
            work_item.module_name,
            work_item.operator_name,
            work_item.occurrence,
            test_runner,
            test_args,
            timeout)
        job_id, command, (result_type, result_data) = result
        yield job_id, command, result_type, result_data


class CeleryExecutor:
    def __init__(self, purge_queue=True):
        self.purge_queue = purge_queue

    def __call__(self, test_runner, test_args, timeout, pending_work):
        try:
            results = cosmic_ray.tasks.worker.execute_work_items(
                test_runner,
                test_args,
                timeout,
                pending_work)

            for r in results:
                job_id, command, (result_type, result_data) = r.get()
                yield job_id, command, result_type, result_data
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
    results = executor(test_runner,
                       test_args,
                       timeout,
                       work_db.pending_work)
    for result in results:
        work_db.add_results(*result)
