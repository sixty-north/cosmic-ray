"Base execution-engine implementation details."

import abc


class ExecutionEngine(metaclass=abc.ABCMeta):
    "Base class for execution engine plugins."

    @abc.abstractmethod
    def __call__(self, pending_work, python_version, test_command, timeout, engine_config, on_task_complete):
        """Execute jobs in `pending_work_items`.

        Spend no more than `timeout` seconds for a single job, using `engine_config` to
        distribute the work.
        """
