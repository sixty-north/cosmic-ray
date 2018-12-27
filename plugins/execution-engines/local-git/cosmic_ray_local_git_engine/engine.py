"Implementation of the local-git execution engine plugin."

import logging
import multiprocessing
import multiprocessing.util
import os
import tempfile
from pathlib import Path

import git

from cosmic_ray.execution.execution_engine import ExecutionEngine
from cosmic_ray.worker import worker

log = logging.getLogger(__name__)

_workspace = None


class Workspace:
    def __init__(self, timeout, config):
        self.timeout = timeout
        self.config = config

        self.tempdir = tempfile.TemporaryDirectory()
        log.info('New local-git workspace in %s', self.tempdir.name)

        self.clone_dir = str(Path(self.tempdir.name) / 'repo')

        repo_uri = config.execution_engine_config.get('repo-uri', '.')
        log.info('Cloning git repo %s to %s', repo_uri, self.clone_dir)
        git.Repo.clone_from(repo_uri, self.clone_dir, depth=1)

    def cleanup(self):
        log.info('Removing temp dir %s', self.tempdir.name)
        self.tempdir.cleanup()


def _initialize_worker(timeout, config):
    global _workspace
    assert _workspace is None

    log.info('Initialize local-git worker in PID %s', os.getpid())
    _workspace = Workspace(timeout, config)

    # Register a finalizer
    multiprocessing.util.Finalize(_workspace, lambda: _workspace.cleanup(), exitpriority=16)


def execute_work_item(work_item):
    log.info('Executing worker in %s, PID=%s', _workspace.clone_dir, os.getpid())

    os.chdir(_workspace.clone_dir)

    result = worker(
        work_item.module_path,
        _workspace.config.python_version,
        work_item.operator_name,
        work_item.occurrence,
        _workspace.config.test_command,
        _workspace.timeout)

    return work_item.job_id, result


class LocalGitExecutionEngine(ExecutionEngine):
    "The local-git execution engine."

    def __call__(self, timeout, pending_work, config, on_task_complete):
        # TODO: One problem with this approach is that we enqueue all of the
        # pending work at once. This could be a huge number of objects. Is there
        # a clean way to flow-control the pipeline? Or am I wrong and it's already
        # being limited for me?

        pool = multiprocessing.Pool(
            initializer=_initialize_worker,
            initargs=(timeout, config))

        results = pool.map(
            func=execute_work_item,
            iterable=pending_work)

        for job_id, result in results:
            on_task_complete(job_id, result)
