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
import logging

import aiohttp

from cosmic_ray.execution.execution_engine import ExecutionEngine
from cosmic_ray.work_item import TestOutcome, WorkerOutcome, WorkItem, WorkResult, WorkItemJsonDecoder

log = logging.getLogger(__name__)


class LocalExecutionEngine(ExecutionEngine):
    "The local execution engine."

    def __call__(self, pending_work, python_version, test_command, timeout, engine_config, on_task_complete):
        # TODO: We still have the issue that `pending_work` is a running query on the database. Will `on_task_complete`
        # - which writes results to the database - be able to complete, or will it be blocked? Do we have to copy the
        # pending work as we used to do?

        # TODO: Will there be an event loop? Where should we ensure that there is?
        asyncio.get_event_loop().run_until_complete(
            self._process(pending_work, python_version, test_command, timeout, engine_config, on_task_complete)
        )

    async def _process(self, pending_work, python_version, test_command, timeout, config, on_task_complete):
        urls = config.get("worker-urls", [])

        if not urls:
            raise ValueError("No worker URLs provided for LocalExecutionEngine")

        fetchers = {}

        async def handle_completed_task(task):
            # TODO: If one of the URLs we've got is bad (i.e. no worker is running on it), that will result in an
            # exception from one of the tasks. We should notice this, log it, and remove the offending URL from the
            # pool.

            url, completed_job_id = fetchers[task]
            try:
                result = await task
            except Exception as exc:
                # TODO: Do something with the exception
                log.exception("Error fetching result")
                result = WorkResult(worker_outcome=WorkerOutcome.ABNORMAL, output=str(exc))
            finally:
                del fetchers[task]
                urls.append(url)
                on_task_complete(completed_job_id, result)

        for work_item in pending_work:
            # Wait for an available URL
            while not urls:
                done, pending = await asyncio.wait(fetchers.keys(), return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    await handle_completed_task(task)

            assert urls, "URL should always be available"

            # Use an available URL to process the task
            url = urls.pop()
            fetcher = asyncio.create_task(fetch(url, work_item, python_version, test_command, timeout))
            fetchers[fetcher] = url, work_item.job_id

        # Drain the remaining work
        done, pending = await asyncio.wait(fetchers.keys(), return_when=asyncio.ALL_COMPLETED)
        for task in done:
            await handle_completed_task(task)


async def fetch(url, work_item: WorkItem, python_version, test_command, timeout):
    parameters = {
        "module_path": str(work_item.module_path),
        "operator": work_item.operator_name,
        "occurrence": work_item.occurrence,
        "python_version": python_version,
        "test_command": test_command,
        "timeout": timeout,
    }
    async with aiohttp.request("POST", url, json=parameters) as resp:
        result = await resp.json()
        # TODO: Account for possibility that `data` is the wrong shape.
        return WorkResult(
            worker_outcome=result["worker_outcome"],
            output=result["output"],
            test_outcome=result["test_outcome"],
            diff=result["diff"],
        )
