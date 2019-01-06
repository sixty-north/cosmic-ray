"""Cosmic Ray execution engine that runs mutations locally on git clones.

This engine creates a pool of subprocesses, each of which execute some portion
of work items in a session. Each of these processes creates a shallow clone of
the git repository containing the code to be mutated/tested in a temporary
directory. This way each process can work independently.

## Enabling the engine

To use the local-git execution engine, set `cosmic-ray.execution-engine.name =
"local-git"` in your Cosmic Ray configuration::

    [cosmic-ray.execution-engine]
    name = "local-git"

## Specifying the source repository

Each subprocess creates its own clone of a source git repository. By default,
the engine determines which repo to use by looking for the repo dominating the
directory in which `cosmic-ray` is executed. However, you can specify a
different repository (e.g. a repo hosted on github) by setting the
`cosmic-ray.execution-engine.local-git.repo-uri`::

    [cosmic-ray.execution-engine.local-git]
    repo-uri = "https://github.com/me/difference-engine-emulator"

## Subprocess environment

The local-git engine launches its subprocesses using the `multiprocessing`
library. As such, the subprocesses run in an environment that is largely
identical to that of the main `cosmic-ray` process.

One major difference is the directory in which the subprocesses run. They run
the root of the cloned repository, so you need to take this into account when
creating the configuration.
"""

import logging
import multiprocessing
import multiprocessing.util
import os

from cosmic_ray.cloning import ClonedWorkspace
from cosmic_ray.execution.execution_engine import ExecutionEngine
from cosmic_ray.worker import worker

log = logging.getLogger(__name__)

# Per-subprocess globals
_workspace = None
_config = None


def _initialize_worker(config):
    # pylint: disable=global-statement
    global _workspace
    global _config

    assert _workspace is None
    assert _config is None

    _config = config

    log.info('Initialize local-git worker in PID %s', os.getpid())
    _workspace = ClonedWorkspace(config.cloning_config)

    # Register a finalizer
    multiprocessing.util.Finalize(_workspace, _workspace.cleanup, exitpriority=16)


def _execute_work_item(work_item):
    log.info('Executing worker in %s, PID=%s', _workspace.clone_dir, os.getpid())

    os.chdir(_workspace.clone_dir)

    result = worker(
        work_item.module_path,
        _config.python_version,
        work_item.operator_name,
        work_item.occurrence,
        _config.test_command(_workspace.python_executable),
        _config.timeout)

    return work_item.job_id, result


class LocalExecutionEngine(ExecutionEngine):
    "The local-git execution engine."

    def __call__(self, pending_work, config, on_task_complete):
        # pylint: disable=W0511
        # TODO: One problem with this approach is that we enqueue all of the
        # pending work at once. This could be a huge number of objects. Is there
        # a clean way to flow-control the pipeline? Or am I wrong and it's already
        # being limited for me?

        pool = multiprocessing.Pool(
            initializer=_initialize_worker,
            initargs=(config,))

        results = pool.map(
            func=_execute_work_item,
            iterable=pending_work)

        for job_id, result in results:
            on_task_complete(job_id, result)
