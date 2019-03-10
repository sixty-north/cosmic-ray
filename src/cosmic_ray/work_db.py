"""Implementation of the WorkDB."""

import contextlib
import os
import sqlite3
from enum import Enum

from .config import deserialize_config, serialize_config
from .work_item import TestOutcome, WorkerOutcome, WorkItem, WorkResult


class WorkDB:
    """WorkDB is the database that keeps track of mutation testing work progress.

    Essentially, there's a row in the DB for each mutation that needs to be
    executed in some run. These initially start off with no results, and
    results are added as they're completed.
    """

    class Mode(Enum):
        "Modes in which a WorkDB may be opened."

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
            raise FileNotFoundError('Requested file {} not found'.format(path))

        self._path = path
        self._conn = sqlite3.connect(path)

        self._init_db()

    def close(self):
        """Close the database."""
        self._conn.close()

    @property
    def name(self):
        """A name for this database.

        Derived from the constructor arguments.
        """
        return self._path

    def set_config(self, config):
        """Set (replace) the configuration for the session.

        Args:
          config: Configuration object
        """
        with self._conn:
            self._conn.execute("DELETE FROM config")
            self._conn.execute('INSERT INTO config VALUES(?)',
                               (serialize_config(config),))

    def get_config(self):
        """Get the work parameters (if set) for the session.

        Returns: a Configuration object.

        Raises:
          ValueError: If is no config set for the session.
        """
        rows = list(self._conn.execute("SELECT * FROM config"))
        if not rows:
            raise ValueError("work-db has no config")
        (config_str,) = rows[0]

        return deserialize_config(config_str)

    @property
    def work_items(self):
        """An iterable of all of WorkItems in the db.

        This includes both WorkItems with and without results.
        """
        cur = self._conn.cursor()
        rows = cur.execute("SELECT * FROM work_items")
        for row in rows:
            yield _row_to_work_item(row)

    @property
    def num_work_items(self):
        """The number of work items."""
        count = self._conn.execute("SELECT COUNT(*) FROM work_items")
        return list(count)[0][0]

    def add_work_item(self, work_item):
        """Add a WorkItems.

        Args:
          work_item: A WorkItem.
        """
        with self._conn:
            self._conn.execute(
                '''
                INSERT INTO work_items
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', _work_item_to_row(work_item))

    def clear(self):
        """Clear all work items from the session.

        This removes any associated results as well.
        """
        with self._conn:
            self._conn.execute('DELETE FROM results')
            self._conn.execute('DELETE FROM work_items')

    @property
    def results(self):
        "An iterable of all `(job-id, WorkResult)`s."
        cur = self._conn.cursor()
        rows = cur.execute("SELECT * FROM results")
        for row in rows:
            yield (row['job_id'], _row_to_work_result(row))

    @property
    def num_results(self):
        """The number of results."""
        count = self._conn.execute("SELECT COUNT(*) FROM results")
        return list(count)[0][0]

    def set_result(self, job_id, result):
        """Set the result for a job.

        This will overwrite any existing results for the job.

        Args:
          job_id: The ID of the WorkItem to set the result for.
          result: A WorkResult indicating the result of the job.

        Raises:
           KeyError: If there is no work-item with a matching job-id.
        """
        with self._conn:
            try:
                self._conn.execute(
                    '''
                    REPLACE INTO results
                    VALUES (?, ?, ?, ?, ?)
                    ''', _work_result_to_row(job_id, result))
            except sqlite3.IntegrityError as exc:
                raise KeyError('Can not add result with job-id {}'.format(
                    job_id)) from exc

    @property
    def pending_work_items(self):
        "Iterable of all pending work items."
        pending = self._conn.execute(
            "SELECT * FROM work_items WHERE job_id NOT IN (SELECT job_id FROM results)"
        )
        return (_row_to_work_item(p) for p in pending)

    @property
    def completed_work_items(self):
        "Iterable of `(work-item, result)`s for all completed items."
        completed = self._conn.execute(
            "SELECT * FROM work_items, results WHERE work_items.job_id == results.job_id"
        )
        return ((_row_to_work_item(result), _row_to_work_result(result))
                for result in completed)

    # @property
    # def num_pending_work_items(self):
    #     "The number of pending WorkItems in the session."
    #     count = self._conn.execute("SELECT COUNT(*) FROM work_items WHERE job_id NOT IN (SELECT job_id FROM results)")
    #     return count[0][0]

    def _init_db(self):
        with self._conn:
            self._conn.row_factory = sqlite3.Row

            self._conn.execute("PRAGMA foreign_keys = 1")

            self._conn.execute('''
            CREATE TABLE IF NOT EXISTS work_items
            (module_path text,
             operator text,
             occurrence int,
             start_line int,
             start_col int,
             end_line int,
             end_col int,
             job_id text primary key)
            ''')

            self._conn.execute('''
            CREATE TABLE IF NOT EXISTS results
            (worker_outcome text,
             output text,
             test_outcome text,
             diff text,
             job_id text primary key,
             FOREIGN KEY(job_id) REFERENCES work_items(job_id)
            )
            ''')

            self._conn.execute('''
            CREATE TABLE IF NOT EXISTS config
            (config text)
            ''')


def _row_to_work_item(row):
    return WorkItem(
        module_path=row['module_path'],
        operator_name=row['operator'],
        occurrence=row['occurrence'],
        start_pos=(row['start_line'], row['start_col']),
        end_pos=(row['end_line'], row['end_col']),
        job_id=row['job_id'])


def _work_item_to_row(work_item):
    return (
        str(work_item.module_path),
        work_item.operator_name,
        work_item.occurrence,
        work_item.start_pos[0],
        work_item.start_pos[1],
        work_item.end_pos[0],
        work_item.end_pos[1],
        work_item.job_id)


def _row_to_work_result(row):
    test_outcome = row['test_outcome']
    test_outcome = None if test_outcome is None else TestOutcome(test_outcome)

    return WorkResult(
        worker_outcome=WorkerOutcome(row['worker_outcome']),
        output=row['output'],
        test_outcome=test_outcome,
        diff=row['diff'])


def _work_result_to_row(job_id, result):
    return (
        result.worker_outcome.value,  # should never be None
        result.output,
        None if result.test_outcome is None else result.test_outcome.value,
        result.diff,
        job_id)


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
    finally:
        database.close()
