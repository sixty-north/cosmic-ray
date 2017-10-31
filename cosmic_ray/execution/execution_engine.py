import abc


class ExecutionEngine(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, timeout, pending_work, config):
        pass
