import cosmic_ray.tasks.worker


def execute(work_db):
    """Execute any pending work in `work_db`, recording the results.

    This looks for any work in `work_db` which has no results, schedules to be
    executed, and records any results that arrive.

    """
    test_runner, test_directory, timeout = work_db.get_work_parameters()
    results = cosmic_ray.tasks.worker.execute_work_items(
        test_runner,
        test_directory,
        timeout,
        work_db.pending_work)

    for r in results:
        job_id, command, (result_type, result_data) = r.get()
        work_db.add_results(job_id, command, result_type, result_data)
