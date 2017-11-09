"Base execution-engine implementation details."

import abc


class ExecutionEngine(metaclass=abc.ABCMeta):
    "Base class for exection engine plugins."
    @abc.abstractmethod
    def __call__(self, timeout, pending_work, config):
        """Execute jobs in `pending_work`, spending no more than `timeout` seconds for
        a single job, using `config` to control the work.
        """
        pass
