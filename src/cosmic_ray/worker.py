"""Workers handle single mutation+test runs.
"""

import contextlib
import logging
import os

from cosmic_ray.cloning import ClonedWorkspace
from cosmic_ray.mutating import mutate_and_test

log = logging.getLogger()


class Worker:
    """Manages a workspace and accepts mutation+test requests.

    A worker clones (e.g. via git, a file copy, or something) the code to be mutated into a private directory. It then
    fields requests to perform a mutation+test which it fulfills by mutating the cloned code.
    """

    def __init__(self, config):
        self._config = None
        self._workspace = None

        self.activate(config)

    def activate(self, config):
        """Create a new cloned workspace from a configuration.

        This replaces any existing clone, cleaning up its resources.
        """
        new_workspace = ClonedWorkspace(config.cloning_config)

        self.cleanup()

        self._config = config
        self._workspace = new_workspace

    def cleanup(self):
        if self._workspace is not None:
            self._workspace.cleanup()

    def execute(self, work_item):
        """Perform a single mutation and test run.

        Args:
            work_item: A `WorkItem` describing the work to do.

        Returns: A `(job-id, WorkResult)` tuple.
        """
        log.info('Executing worker in %s, PID=%s',
                 self._workspace.clone_dir, os.getpid())

        with excursion(self._workspace.clone_dir):
            result = mutate_and_test(
                work_item.module_path,
                self._config.python_version,
                work_item.operator_name,
                work_item.occurrence,
                self._config.test_command,
                self._config.timeout)

        return work_item.job_id, result


@contextlib.contextmanager
def excursion(dirname):
    "Context manager for temporarily changing directories."
    orig = os.getcwd()
    try:
        os.chdir(dirname)
        yield
    finally:
        os.chdir(orig)
