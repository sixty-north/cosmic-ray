"""A tool for launching HTTP workers and executing a session using them.

This reads the 'distributor.http.worker-urls' field of a config to see where workers are expected to be
running. For each worker, it makes a clone of the git repository that's going to be tested, optionally changing to a
directory under the root of the clone before starting the worker. It then starts the workers with the correct options to
provide the configured URLs.
"""

import asyncio
import logging
import tempfile
from pathlib import Path

import click
import git
import yarl

import cosmic_ray.config

log = logging.getLogger()


async def run(config_file, repo_url, location):
    """Start the configured workers on the own git clones.

    Args:
        config_file: The Cosmic Ray configuration file describing the distributor URLs.
        repo_url: The git repository to clone for each worker.
        location: The relative path into the cloned repository to use as the cwd for
            each worker.
    """
    config = cosmic_ray.config.load_config(config_file)
    worker_urls = config.sub("distributor", "http").get("worker-urls", ())

    worker_args = tuple(_urls_to_args(worker_urls, Path(config_file).resolve()))
    if not worker_args:
        log.warning("No valid worker URLs found in config %s", config_file)

    with tempfile.TemporaryDirectory() as root:
        for idx, _ in enumerate(worker_args):
            _create_clone(repo_url, Path(root) / str(idx))

        procs = [
            await asyncio.create_subprocess_shell(
                f"cosmic-ray --verbosity INFO http-worker {option} {value}", cwd=Path(root) / str(idx) / location
            )
            for idx, (option, value) in enumerate(worker_args)
        ]

        await asyncio.gather(*[proc.communicate() for proc in procs])


@click.command(help=__doc__)
@click.argument("config_file", type=click.Path(exists=True, dir_okay=False, readable=True))
@click.argument("repo_url")
@click.option("--location", default="", help="The relative path under a repo clone at which to run the worker")
def main(config_file, repo_url, location):
    logging.basicConfig(level=logging.INFO)
    asyncio.get_event_loop().run_until_complete(run(config_file, repo_url, location))


def _create_clone(source_repo_url, destination_dir):
    url = yarl.URL(source_repo_url)
    if url.scheme == "":
        url = yarl.URL.build(scheme="file", path=str(Path(url.path).resolve()))

    log.info("Cloning %s to %s", url, destination_dir)
    git.Repo.clone_from(str(url), destination_dir, depth=1)


LOCALHOST_ADDRESSES = (
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
)


def _urls_to_args(urls, config_filepath: Path):
    for url in urls:
        url = yarl.URL(url)
        if url.scheme == "":
            socket_path = config_filepath.parent / url.path
            yield ("--path", socket_path)
        elif url.scheme in ("http", "https"):
            if url.port is None:
                log.warning("HTTP(S) URL %s has no port", url)

            elif url.host.lower() not in LOCALHOST_ADDRESSES:
                log.warning("%s does not appear to be on localhost", url)

            else:
                yield ("--port", url.port)
        else:
            log.warning("The scheme of URL %s is not supported", url)


if __name__ == "__main__":
    main()
