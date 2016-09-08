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
#  - test args
#  - timeout
#
# What describes results?
#  - one of the strings 'exception', 'no-test', or 'normal'
#  - for 'exception', the sys.exc_info() of the exception
#  - for 'no-test', there are no other results
#  - for 'normal', there is an *activation-record* (a dict) and a
#    test_runner.TestResult.

import collections
import contextlib
from enum import Enum
import os

# This db may well not scale very well. We need to be ready to switch it out
# for something quicker if not. But for now it's *very* convenient.
import tinydb


WorkItem = collections.namedtuple('WorkItem',
                                  ['work_id',
                                   'module_name',
                                   'operator_name',
                                   'occurrence',
                                   'command',
                                   'result_type',
                                   'result_data'])


def _make_work_item(rec):
    return WorkItem(
        rec.eid,
        rec['module-name'],
        rec['op-name'],
        rec['occurrence'],
        rec.get('command', None),
        rec.get('result-type', None),
        rec.get('result-data', None))


class WorkDB:
    class Mode(Enum):
        # Open existing files, creating if necessary
        create = 1,

        # Open only existing files, failing if it doesn't exist
        open = 2

    def __init__(self, path, mode):
        """Open a DB in file `path` in mode `mode`.

        Args:
          path: The path to the DB file.
          mode: The mode in which to open the DB. See the `Mode` enum for
            details.

        Raises:
          FileNotFoundError: If `mode` is `Mode.open` and `path` does not
            exist.
        """
        if (mode == WorkDB.Mode.open) and (not os.path.exists(path)):
            raise FileNotFoundError(
                'Requested file {} not found'.format(path))

        self._db = tinydb.TinyDB(path)

    def close(self):
        self._db.close()

    @property
    def _work_parameters(self):
        """The table of work parameters."""
        return self._db.table('work-parameters')

    @property
    def _work_items(self):
        """The table of work items."""
        return self._db.table('work-items')

    def set_work_parameters(self, test_runner, test_args, timeout):
        """Set (replace) the work parameters for the session.

        Args:
          test_runner: The name of the test runner plugin to use.
          test_args: The arguments to pass to the test runner.
          timeout: The timeout for tests.
        """
        table = self._work_parameters
        table.purge()
        table.insert({
            'test-runner': test_runner,
            'test-args': test_args,
            'timeout': timeout,
        })

    def get_work_parameters(self):
        """Get the work parameters (if set) for the session.

        Returns: a tuple of `(test-runner, test-args, timeout)`.

        Raises:
          ValueError: If there are no work parameters set for the session.
        """
        table = self._work_parameters

        try:
            record = table.all()[0]
        except IndexError:
            raise ValueError('work-db has no work parameters')

        return (record['test-runner'],
                record['test-args'],
                record['timeout'])

    def add_work_items(self, items):
        """Add a sequence of new work items to the session.

        These are added with no associated results and will be considered
        "pending".

        Args:
          items: An iterable of tuples of the form `(module-name,
            operator-name, occurrence)`.

        """
        table = self._work_items
        table.insert_multiple(
            {'module-name': i[0],
             'op-name': i[1],
             'occurrence': i[2]}
            for i in items)

    def clear_work_items(self):
        """Clear all work items from the session.

        This removes any associated results as well.
        """
        self._work_items.purge()

    @property
    def work_items(self):
        """The sequence of `WorkItem`s in the session.

        This include both complete and incomplete items.

        Each work item is a dict with the keys `module-name`, `op-name`, and
        `occurrence`. Items with results will also have the keys `results-type`
        and `results-data`.

        """
        return (_make_work_item(r) for r in self._work_items.all())

    def add_results(self, job_id, command, results_type, results_data):
        """Add a result to the session for the work-item with id `job_id`.

        Args:
          job_id: The ID of the work-item to update.
          results_type: One of 'exception', 'no-test', or 'normal'.
          results_data: The associated data, if any.

        Raises:
          KeyError: If there is no work-item with the id `job_id`.
        """
        table = self._work_items
        table.update(
            {
                'command': command,
                'result-type': results_type,
                'result-data': results_data,
            },
            eids=[job_id])

    @property
    def pending_work(self):
        """The sequence of pending `WorkItem`s in the session."""
        table = self._work_items
        work_item = tinydb.Query()

        return (_make_work_item(record)
                for record
                in table.search(~ work_item['result-type'].exists()))


@contextlib.contextmanager
def use_db(path, mode=WorkDB.Mode.create):
    """
    Open a DB in file `path` in mode `mode` as a context manager.

    On exiting the context the DB will be automatically closed.

    Args:
      path: The path to the DB file.
      mode: The mode in which to open the DB. See the `Mode` enum for
        details.

    Raises:
      FileNotFoundError: If `mode` is `Mode.open` and `path` does not
        exist.
    """
    db = WorkDB(path, mode)
    try:
        yield db
    except Exception:
        db.close()
        raise
