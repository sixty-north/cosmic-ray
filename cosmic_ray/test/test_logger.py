from io import StringIO
import unittest

from cosmic_ray.app import Logger
from cosmic_ray.mutating import MutationRecord
from cosmic_ray.testing.test_runner import Outcome, TestResult


class LoggerTest(unittest.TestCase):
    def setUp(self):
        self._file_like = StringIO()
        self._logger = Logger.start(file_like=self._file_like).proxy()

    def tearDown(self):
        self._logger.stop()

    def _stop_logger(self):
        self._logger.stop()
        self._logger.actor_stopped.get().wait()

    def test_records_are_recorded(self):
        mutation_record = MutationRecord(
            'foo', 'foo.py', 'operator',
            {'description': 'desc',
             'line_number': 3},
            None)
        test_result = TestResult(Outcome.KILLED, 'ok')

        self._logger.handle_result(mutation_record, test_result)
        self._stop_logger()
        self._file_like.flush()
        self._file_like.seek(0)

        self.assertGreater(len(self._file_like.read()), 0)
