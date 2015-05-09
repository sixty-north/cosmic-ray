import unittest

from cosmic_ray.app import Summarizer
from cosmic_ray.mutating import MutationRecord
from cosmic_ray.testing.test_runner import Outcome, TestResult


class SummarizerTest(unittest.TestCase):
    def setUp(self):
        self._summarizer = Summarizer.start().proxy()

    def tearDown(self):
        self._stop_summarizer()

    def _stop_summarizer(self):
        self._summarizer.stop()
        self._summarizer.actor_stopped.get().wait()

    def _check_outcomes(self, survived, killed, incompetent):
        self.assertEqual(self._summarizer.outcomes.get()[Outcome.SURVIVED],
                         survived)
        self.assertEqual(self._summarizer.outcomes.get()[Outcome.KILLED],
                         killed)
        self.assertEqual(self._summarizer.outcomes.get()[Outcome.INCOMPETENT],
                         incompetent)

    def test_statistics_are_correct(self):
        mutation_record = MutationRecord(
            'foo', 'foo.py', 'operator',
            {'description': 'desc',
             'line_number': 3},
            None)

        self._summarizer.handle_result(
            mutation_record,
            TestResult(Outcome.SURVIVED, 'ok'))
        self._check_outcomes(1, 0, 0)

        self._summarizer.handle_result(
            mutation_record,
            TestResult(Outcome.KILLED, 'ok'))
        self._check_outcomes(1, 1, 0)

        self._summarizer.handle_result(
            mutation_record,
            TestResult(Outcome.INCOMPETENT, 'ok'))
        self._check_outcomes(1, 1, 1)
