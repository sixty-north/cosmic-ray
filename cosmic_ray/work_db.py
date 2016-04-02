# Database that keeps track of mutation testing work progress.
#
# Essentially, there's a row in the DB for each mutation that needs to be
# executed in some run. These initially start off with no results, and results
# are added as they're completed.
#
# What describes a work-item?
#  - module name
#  - operator name
#  - occurrence
#  - test runner name
#  - test directory
#  - timeout
#
# What describes results?
#  - one of the strings 'exception', 'no-test', or 'normal'
#  - for 'exception', the sys.exc_info() of the exception
#  - for 'no-test', there are no other results
#  - for 'normal', there is an *activation-record* (a dict) and a
#    test_runner.TestResult.

import contextlib

import tinydb


class WorkDB:
    def __init__(self, path):
        self._db = tinydb.TinyDB(path)

    def close(self):
        self._db.close()

    @property
    def _work_parameters(self):
        return self._db.table('work-parameters')

    @property
    def _work_items(self):
        return self._db.table('work-items')

    def set_work_parameters(self, test_runner, test_directory, timeout):
        table = self._work_parameters
        table.purge()
        table.insert({
            'test-runner': test_runner,
            'test-directory': test_directory,
            'timeout': timeout,
        })

    def get_work_parameters(self):
        table = self._work_parameters

        try:
            record = table.all()[0]
        except IndexError:
            raise ValueError('work-db has no work parameters')

        return (record['test-runner'],
                record['test-directory'],
                record['timeout'])

    def add_work_items(self, items):
        table = self._work_items
        table.insert_multiple(
            {'module-name': i[0],
             'op-name': i[1],
             'occurrence': i[2]}
            for i in items)

    def clear_work_items(self):
        self._work_items.purge()

    @property
    def work_items(self):
        return self._work_items.all()

    def add_results(self, job_id, results_type, results_data):
        table = self._work_items
        table.update(
            {
                'results-type': results_type,
                'results-data': results_data,
            },
            eids=[job_id])

    @property
    def pending_work(self):
        table = self._work_items
        work_item = tinydb.Query()

        return ((record.eid,
                 record['module-name'],
                 record['op-name'],
                 record['occurrence'])
                for record
                in table.search(~ work_item['results-type'].exists()))


@contextlib.contextmanager
def use_db(path):
    db = WorkDB(path)
    try:
        yield db
    except Exception:
        db.close()
        raise
