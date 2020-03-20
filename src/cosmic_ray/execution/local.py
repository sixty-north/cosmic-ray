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

from cosmic_ray.execution.execution_engine import ExecutionEngine
from cosmic_ray.worker import Worker

log = logging.getLogger(__name__)

# Per-subprocess globals
_worker = None


def _initialize_worker(config):
    # pylint: disable=global-statement
    global _worker
    assert _worker is None

    _worker = Worker(config)

    log.info('Initialize local-git worker in PID %s', os.getpid())
 
    # Register a finalizer
    multiprocessing.util.Finalize(
        _worker, _worker.cleanup, exitpriority=16)


def _execute_work_item(work_item):
    return _worker.execute(work_item)


class LocalExecutionEngine(ExecutionEngine):
    "The local-git execution engine."

    def __call__(self, pending_work, config, on_task_complete):
        with multiprocessing.Pool(
                initializer=_initialize_worker,
                initargs=(config,)) as pool:

            # pylint: disable=W0511
            # TODO: This is not optimal. The pending-work iterable could be millions
            # or billions of elements. We don't want to copy it. We copy it right
            # now so that we don't access the database in a separate thread (i.e.
            # one created by imap_unoredered below). We need to find a way around
            # this.
            pending = list(pending_work)

            results = pool.imap_unordered(
                func=_execute_work_item,
                iterable=pending)

            for job_id, result in results:
                on_task_complete(job_id, result)
