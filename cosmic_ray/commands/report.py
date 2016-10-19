def _print_item(item, full_report):
    result = item.result_data
    result_type = item.result_type
    if result_type in ['normal', 'exception']:
        result_type = result[1][0]
    ret_val = [
        'job ID {}:{}:{}'.format(
            item.work_id,
            result_type,
            item.module_name),
        'command: {}'.format(
            ' '.join(item.command)
            if item.command is not None else ''),
    ]
    if result_type == 'Outcome.KILLED' and not full_report:
        ret_val = []
    elif item.result_type == 'timeout':
        if full_report:
            ret_val.append("timeout: {:.3f} sec".format(result))
        else:
            ret_val = []
    elif item.result_type in ['normal', 'exception']:
        ret_val += result[1][1]

    # for presentation purposes only
    if ret_val:
        ret_val.append('')

    return ret_val


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


def create_report(work_db, show_pending, full_report=False):
    for item in work_db.work_items:
        if (item.result_type is not None) or show_pending:
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
