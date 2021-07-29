"""Cosmic Ray distributor that sends work requests over HTTP to workers.

This uses a list of URLs to workes, distributing work to them as they're available.

Enabling the distributor
========================

To use the local distributor, set ``cosmic-ray.distributor.name = "http"`` in your Cosmic Ray configuration, and
configure the list of worker URLs in ``cosmic-ray.distributor.http.worker-urls``:

.. code-block:: toml

    [cosmic-ray.distributor]
    name = "http"

    [cosmic-ray.distributor.http]
    worker-urls = ['http://localhost:9876', 'http://localhost:9877']
"""
import asyncio
import logging
from pathlib import Path

import aiohttp
from aiohttp import web
from cosmic_ray.distribution.distributor import Distributor
from cosmic_ray.mutating import mutate_and_test
from cosmic_ray.work_item import MutationSpec, WorkerOutcome, WorkItem, WorkResult

log = logging.getLogger(__name__)


class HttpDistributor(Distributor):
    """The http distributor.

    This forwards mutate-and-test requests to HTTP servers which do the actual work and
    return the results.
    """

    def __call__(self, *args, **kwargs):
        # TODO: We still have the issue that `pending_work` is a running query on the database. Will `on_task_complete`
        # - which writes results to the database - be able to complete, or will it be blocked? Do we have to copy the
        # pending work as we used to do?

        # TODO: Will there be an event loop? Where should we ensure that there is?
        asyncio.get_event_loop().run_until_complete(self._process(*args, **kwargs))

    async def _process(self, pending_work, test_command, timeout, config, on_task_complete):
        urls = config.get("worker-urls", [])

        if not urls:
            raise ValueError("No worker URLs provided for HttpDistributor")

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
                assert fetchers.keys()
                done, pending = await asyncio.wait(fetchers.keys(), return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    await handle_completed_task(task)

            assert urls, "URL should always be available"

            # Use an available URL to process the task
            url = urls.pop()
            fetcher = asyncio.create_task(send_request(url, work_item, test_command, timeout))
            fetchers[fetcher] = url, work_item.job_id

        # Drain the remaining work
        if fetchers.keys():
            done, pending = await asyncio.wait(fetchers.keys(), return_when=asyncio.ALL_COMPLETED)
            for task in done:
                await handle_completed_task(task)


async def send_request(url, work_item: WorkItem, test_command, timeout):
    """Sends a mutate-and-test request to a worker.

    Args:
        url: The URL of the worker.
        work_item: The `WorkItem` representing the work to be done.
        test_command: The command that the worker should use to run the tests.
        timeout: The maximum number of seconds to spend running the test.

    Returns: A `WorkResult`.
    """
    parameters = {
        "mutations": [
            {
                "module_path": str(mutation.module_path),
                "operator": mutation.operator_name,
                "occurrence": mutation.occurrence,
            }
            for mutation in work_item.mutations
        ],
        "test_command": test_command,
        "timeout": timeout,
    }
    log.info("Sending HTTP request to %s", url)
    async with aiohttp.request("POST", url, json=parameters) as resp:
        result = await resp.json()
        # TODO: Account for possibility that `data` is the wrong shape.
        return WorkResult(
            worker_outcome=result["worker_outcome"],
            output=result["output"],
            test_outcome=result["test_outcome"],
            diff=result["diff"],
        )


async def handle_mutate_and_test(request):
    """HTTP endpoint handler for requests to mutate-and-test."""
    args = await request.json()
    result = await mutate_and_test(
        mutations=[
            MutationSpec(
                module_path=Path(mutation["module_path"]),
                operator_name=mutation["operator"],
                occurrence=mutation["occurrence"],
            )
            for mutation in args["mutations"]
        ],
        test_command=args["test_command"],
        timeout=args["timeout"],
    )
    # TODO: Deal with exceptions. There generally won't be any, so we can just return an abnormal result if there it.

    return web.json_response(
        {
            "worker_outcome": result.worker_outcome.value,
            "output": result.output,
            "test_outcome": result.test_outcome.value if result.test_outcome is not None else None,
            "diff": result.diff,
        }
    )


def run_worker(port=None, path=None):
    """Run the worker HTTP server.

    You must specify either `port` or `path`, but not both.

    Args:
        port: The TCP port on which to listen.
        path: Path to Unix domain socket on which to listen.
    """
    if port is None and path is None:
        raise ValueError("Worker requires either a port or domain socket path")
    app = web.Application()
    app.add_routes([web.post("/", handle_mutate_and_test)])
    web.run_app(app, port=port, path=path)
