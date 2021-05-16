"Base distributor implementation details."

import abc


class Distributor(metaclass=abc.ABCMeta):
    "Base class for work distribution strategies."

    @abc.abstractmethod
    def __call__(self, pending_work, test_command, timeout, distributor_config, on_task_complete):
        """Execute jobs in `pending_work_items`.

        Spend no more than `timeout` seconds for a single job, using `distributor_config` to
        distribute the work.
        """
