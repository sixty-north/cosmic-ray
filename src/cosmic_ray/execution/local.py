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
import asyncio
import concurrent.futures
import contextlib
import logging
import multiprocessing
import multiprocessing.util
import os
from typing import Iterable, Callable

from cosmic_ray.cloning import ClonedWorkspace
from cosmic_ray.config import ConfigDict
from cosmic_ray.execution.execution_engine import ExecutionEngine
from cosmic_ray.work_item import WorkItem
from cosmic_ray.worker import worker

log = logging.getLogger(__name__)

# Per-subprocess globals
_workspace = None
_config = None


@contextlib.contextmanager
def excursion(dirname):
    orig = os.getcwd()
    try:
        os.chdir(dirname)
        yield
    finally:
        os.chdir(orig)


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

    with excursion(_workspace.clone_dir):
        result = worker(
            work_item.module_path,
            _config.python_version,
            work_item.operator_name,
            work_item.occurrence,
            _config.test_command,
            _config.timeout)

    return work_item.job_id, result


class LocalExecutionEngine(ExecutionEngine):
    "The local-git execution engine."

    def __call__(self, pending_work, config, on_task_complete):
        asyncio.run(self._execute_pending_works(pending_work, config, on_task_complete))

    async def _execute_pending_works(self,
                                     pending_work: Iterable[WorkItem],
                                     config: ConfigDict,
                                     on_task_complete: Callable):
        loop = asyncio.get_running_loop()

        with concurrent.futures.ProcessPoolExecutor(
                initializer=_initialize_worker,
                initargs=(config,)
        ) as pool:

            async def run_task(work_item):
                result = await loop.run_in_executor(pool, _execute_work_item,
                                                    work_item)
                on_task_complete(*result)

            tasks = [run_task(work_item) for work_item in pending_work]
            await asyncio.gather(*tasks)
