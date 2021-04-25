"""Cosmic Ray distributor that sends work requests over HTTP to workers.

This uses a list of URLs to workes, distributing work to them as they're available.

## Enabling the engine

To use the local distributor, set `cosmic-ray.distributor.name = "local"` in your Cosmic Ray configuration, and
configure the list of worker URLs in `cosmic-ray.distributor.local.worker-urls`::

    [cosmic-ray.distributor]
    name = "local"

    [cosmic-ray.distributor.local]
    worker-urls = ['http://localhost:9876', 'http://localhost:9877']
"""

import asyncio
import logging

import aiohttp

from cosmic_ray.distribution.distributor import Distributor
from cosmic_ray.work_item import WorkerOutcome, WorkItem, WorkResult

log = logging.getLogger(__name__)


class LocalDistributor(Distributor):
    "The local distributor."

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
