"Base execution-engine implementation details."

import abc


class ExecutionEngine(metaclass=abc.ABCMeta):
    "Base class for execution engine plugins."
    @abc.abstractmethod
    def __call__(self, timeout, pending_work, config, on_task_complete):
        """Execute jobs in `pending_work_items`.

        Spend no more than `timeout` seconds for
        a single job, using `config` to control the work.
        """
        pass
