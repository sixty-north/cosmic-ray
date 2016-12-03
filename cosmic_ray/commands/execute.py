import cosmic_ray.tasks.celery
import cosmic_ray.tasks.worker


def execute(work_db, purge_queue=True):
    """Execute any pending work in `work_db`, recording the results.

    This looks for any work in `work_db` which has no results, schedules to be
    executed, and records any results that arrive.

    """
    test_runner, test_args, timeout = work_db.get_work_parameters()
    try:
        results = cosmic_ray.tasks.worker.execute_work_items(
            test_runner,
            test_args,
            timeout,
            work_db.pending_work)

        for r in results:
            job_id, command, (result_type, result_data) = r.get()
            work_db.add_results(job_id, command, result_type, result_data)
    finally:
        if purge_queue:
            cosmic_ray.tasks.celery.app.control.purge()


def local_execute(work_db):
    test_runner, test_args, timeout = work_db.get_work_parameters()
    for work_item in work_db.pending_work:
        result = cosmic_ray.tasks.worker.worker_task(
            work_item.work_id,
            work_item.module_name,
            work_item.operator_name,
            work_item.occurrence,
            test_runner,
            test_args,
            timeout)
        job_id, command, (result_type, result_data) = result
        work_db.add_results(job_id, command, result_type, result_data)
