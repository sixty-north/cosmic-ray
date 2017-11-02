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

import contextlib
import os
from enum import Enum

# This db may well not scale very well. We need to be ready to switch it out
# for something quicker if not. But for now it's *very* convenient.
import tinydb

from .work_record import WorkRecord


class WorkDB:
    class Mode(Enum):
        # Open existing files, creating if necessary
        create = 1

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
    def _config(self):
        """The table of work parameters."""
        return self._db.table('config')

    @property
    def _work_items(self):
        """The table of work items."""
        return self._db.table('work-items')

    def set_config(self, config, timeout):
        """Set (replace) the configuration for the session.

        Args:
          config: Configuration object
          timeout: The timeout for tests.
        """
        table = self._config
        table.purge()
        table.insert({
            'config': config,
            'timeout': timeout,
        })

    def get_config(self):
        """Get the work parameters (if set) for the session.

        Returns: a tuple of `(config, timeout)`.

        Raises:
          ValueError: If is no config set for the session.
        """
        table = self._config

        try:
            record = table.all()[0]
        except IndexError:
            raise ValueError('work-db has no config')

        return (record['config'],
                record['timeout'])

    def add_work_records(self, records):
        """Add a sequence of WorkRecords.

        Args:
          records: An iterable of tuples of the form `(module-name,
            operator-name, occurrence)`.

        """
        self._work_items.insert_multiple(records)

    def clear_work_records(self):
        """Clear all work items from the session.

        This removes any associated results as well.
        """
        self._work_items.purge()

    @property
    def work_records(self):
        """The sequence of `WorkItem`s in the session.

        This include both complete and incomplete items.

        Each work item is a dict with the keys `module-name`, `op-name`, and
        `occurrence`. Items with results will also have the keys `results-type`
        and `results-data`.

        """
        return (WorkRecord(r) for r in self._work_items.all())

    def update_work_record(self, work_record):
        """Updates an existing WorkRecord by job_id.

        Args:
            work_record: A WorkRecord representing the new state of a job.

        Raises:
          KeyError: If there is no existing record with the same job_id.
        """
        self._work_items.update(
            work_record,
            tinydb.Query().job_id == work_record.job_id)

    @property
    def pending_work(self):
        """The sequence of pending `WorkItem`s in the session."""
        table = self._work_items
        work_item = tinydb.Query()

        # This somewhat tortured invocation is intended to appease linters.
        # They *hate* seeing "x == None" which is the natural expression of
        # this query, so we use this custom test instead.
        pending = table.search(
            work_item.worker_outcome.test(
                lambda val: val is None))

        return (WorkRecord(r) for r in pending)


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
    database = WorkDB(path, mode)
    try:
        yield database
    except Exception:
        raise
    finally:
        database.close()
