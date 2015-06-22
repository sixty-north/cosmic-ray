import unittest

from cosmic_ray.processing import QueueManager


class QueueManagerTest(unittest.TestCase):
    """Testcase for the QueueManager actor.
    """
    def test_iteration_produces_sequence(self):
        """The QueueManager will produce the input sequence you hand it.
        """
        size = 10
        qm = QueueManager.start(range(size)).proxy()
        try:
            for i in range(size):
                self.assertEqual(i, qm.next().get())
        finally:
            qm.stop()

    def test_none_produced_after_iteration(self):
        """The QueueManager will produce None values after it exhausts its
        input sequence.
        """
        size = 10
        qm = QueueManager.start(range(size)).proxy()
        try:
            for i in range(size):
                qm.next().get()
            self.assertIs(qm.next().get(), None)
        finally:
            qm.stop()
