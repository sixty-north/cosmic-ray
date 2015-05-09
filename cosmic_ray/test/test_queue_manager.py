import unittest

from cosmic_ray.app import QueueManager


class QueueManagerTest(unittest.TestCase):
    def test_iteration_produe_sequence(self):
        size = 10
        qm = QueueManager.start(range(size)).proxy()
        try:
            for i in range(size):
                self.assertEqual(i, qm.next().get())
        finally:
            qm.stop()

    def test_none_produced_after_iteration(self):
        size = 10
        qm = QueueManager.start(range(size)).proxy()
        try:
            for i in range(size):
                qm.next().get()
            self.assertIs(qm.next().get(), None)
        finally:
            qm.stop()
