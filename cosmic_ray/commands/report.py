from cosmic_ray.testing.test_runner import TestOutcome
from cosmic_ray.worker import WorkerOutcome


def _print_item(work_record, full_report):
    data = work_record.data
    outcome = work_record.worker_outcome
    if outcome in [WorkerOutcome.NORMAL, WorkerOutcome.EXCEPTION]:
        outcome = work_record.test_outcome
    ret_val = [
        'job ID {}:{}:{}'.format(
            work_record.job_id,
            outcome,
            work_record.module),
        'command: {}'.format(
            ' '.join(work_record.command_line)
            if work_record.command_line is not None else ''),
    ]
    if outcome == TestOutcome.KILLED and not full_report:
        ret_val = []
    elif work_record.worker_outcome == WorkerOutcome.TIMEOUT:
        if full_report:
            ret_val.append("timeout: {:.3f} sec".format(data))
        else:
            ret_val = []
    elif work_record.worker_outcome in [WorkerOutcome.NORMAL, WorkerOutcome.EXCEPTION]:
        ret_val += data
        ret_val += work_record.diff

    # for presentation purposes only
    if ret_val:
        ret_val.append('')

    return ret_val


def _get_kills(db):
    def _keep(w):
        if w.worker_outcome == WorkerOutcome.TIMEOUT:
            return True
        elif w.worker_outcome == WorkerOutcome.NORMAL:
            if w.test_outcome == TestOutcome.KILLED:
                return True
        return False

    return list(filter(_keep, db.work_records))


def _base_stats(work_db):
    total_jobs = sum(1 for _ in work_db.work_records)
    pending_jobs = sum(1 for _ in work_db.pending_work)
    completed_jobs = total_jobs - pending_jobs
    kills = _get_kills(work_db)
    return (total_jobs, pending_jobs, completed_jobs, kills)


def create_report(work_db, show_pending, full_report=False):
    for item in work_db.work_records:
        if (item.worker_outcome is not None) or show_pending:
            yield from _print_item(item, full_report)

    total_jobs, _, completed_jobs, kills = _base_stats(work_db)
    yield 'total jobs: {}'.format(total_jobs)

    if completed_jobs > 0:
        yield 'complete: {} ({:.2f}%)'.format(
            completed_jobs, completed_jobs / total_jobs * 100)
        yield 'survival rate: {:.2f}%'.format(
            (1 - len(kills) / completed_jobs) * 100)
    else:
        yield 'no jobs completed'


def survival_rate(work_db):
    _, _, completed_jobs, kills = _base_stats(work_db)

    if not completed_jobs:
        return 0

    return (1 - len(kills) / completed_jobs) * 100
