def _print_item(item):
    return [
        'job ID: {}'.format(item.work_id),
        'module: {}'.format(item.module_name),
        'operator: {}'.format(item.operator_name),
        'occurrence: {}'.format(item.occurrence),
        'command: {}'.format(
            ' '.join(item.command)
            if item.command is not None else ''),
        'result type: {}'.format(item.result_type),
        'data: {}'.format(item.result_data)
        ]


def _get_kills(db):
    def _keep(w):
        if w.result_type == 'timeout':
            return True
        elif w.result_type == 'normal':
            if w.result_data[1][0] == 'Outcome.KILLED':
                return True
        return False

    return list(filter(_keep, db.work_items))


def _base_stats(work_db):
    total_jobs = sum(1 for _ in work_db.work_items)
    pending_jobs = sum(1 for _ in work_db.pending_work)
    completed_jobs = total_jobs - pending_jobs
    kills = _get_kills(work_db)
    return (total_jobs, pending_jobs, completed_jobs, kills)


def create_report(work_db, show_pending):
    for item in work_db.work_items:
        if (item.result_type is not None) or show_pending:
            yield from _print_item(item)
            yield ''

    total_jobs, pending_jobs, completed_jobs, kills = _base_stats(work_db)
    yield 'total jobs: {}'.format(total_jobs)

    if completed_jobs > 0:
        yield 'complete: {} ({:.2f}%)'.format(
            completed_jobs, completed_jobs / total_jobs * 100)
        yield 'survival rate: {:.2f}%'.format(
            (1 - len(kills) / completed_jobs) * 100)
    else:
        yield 'no jobs completed'


def survival_rate(work_db):
    total_jobs, pending_jobs, completed_jobs, kills = _base_stats(work_db)

    if not completed_jobs:
        return 0

    return (1 - len(kills) / completed_jobs) * 100
