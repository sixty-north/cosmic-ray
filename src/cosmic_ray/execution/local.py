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

import contextlib
import logging
import multiprocessing
import multiprocessing.util
import os
from _queue import Empty
from multiprocessing import Queue

from cosmic_ray.cloning import ClonedWorkspace
from cosmic_ray.execution.execution_engine import ExecutionEngine
from cosmic_ray.testing import run_tests
from cosmic_ray.work_item import WorkResult, WorkerOutcome, TestOutcome
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


def _execute_no_mutate():
    log.info('Executing worker in %s, PID=%s', _workspace.clone_dir, os.getpid())

    with excursion(_workspace.clone_dir):
        test_outcome, output = run_tests(_config.test_command, _config.timeout)
        if test_outcome == TestOutcome.SURVIVED:
            worker_outcome = WorkerOutcome.NORMAL
        else:
            worker_outcome = WorkerOutcome.ABNORMAL

        return WorkResult(
            output=output,
            test_outcome=test_outcome,
            worker_outcome=worker_outcome)


class LocalExecutionEngine(ExecutionEngine):
    "The local-git execution engine."

    def __call__(self, pending_work, config, on_task_complete):
        with multiprocessing.Pool(
                initializer=_initialize_worker,
                initargs=(config,)) as pool:

            log.info("Running initial work")
            result = pool.apply(_execute_no_mutate)
            on_task_complete("no mutation", result)
            if result.worker_outcome != WorkerOutcome.NORMAL:
                return

            result_queue = Queue()
            pending_task_numbers = 0

            def consume_next_result_generator():
                nonlocal pending_task_numbers
                while pending_task_numbers > 0:
                    yield
                    try:
                        result = result_queue.get_nowait()
                        pending_task_numbers -= 1
                        on_task_complete(*result)
                    except Empty:
                        pass

            consume_next_result = consume_next_result_generator()

            def execution_done(result):
                result_queue.put(result)

            def execution_on_error(result):
                log.info("Execution_ error %s", result)

            for work_item in pending_work:
                if work_item.job_id != "no mutation":
                    pending_task_numbers += 1
                    pool.apply_async(_execute_work_item, (work_item,),
                                     callback=execution_done,
                                     error_callback=execution_on_error)

                    next(consume_next_result)
                    # here, we now that next can' raise StopIteration:
                    # len(consume_next_result) >= len(pending_work)

            pool.close()
            pool.join()

            for _ in consume_next_result:
                pass
