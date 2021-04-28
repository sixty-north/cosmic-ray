"""A tool for launching HTTP workers and executing a session using them.
"""

from pathlib import Path
import tempfile

import git
import cosmic_ray.config
import logging
import click
import yarl
import asyncio

log = logging.getLogger()


def create_clone(source_repo_url, destination_dir):
    url = yarl.URL(source_repo_url)
    if url.scheme == "":
        url = yarl.URL.build(scheme="file", path=Path(url.path).resolve())

    log.info("Cloning %s to %s", url, destination_dir)
    git.Repo.clone_from(str(url), destination_dir, depth=1)


async def run(repo_url, ports, location):
    with tempfile.TemporaryDirectory() as root:
        for port in ports:
            create_clone(repo_url, Path(root) / str(port))

        procs = [
            await asyncio.create_subprocess_shell(
                f"cosmic-ray --verbosity INFO http-worker --port {port}", cwd=Path(root) / str(port) / location
            )
            for port in ports
        ]

        await asyncio.gather([await proc.communicate() for proc in procs])


# TODO: We should be reading the config and determining how to run servers based on the
# cosmic-ray.distributor.http.worker-urls option.


@click.command()
@click.argument("repo_url")
@click.argument("port", nargs=-1)
@click.option("--location", default="")
def main(repo_url, port, location):
    logging.basicConfig(level=logging.INFO)
    asyncio.get_event_loop().run_until_complete(run(repo_url, port, location))


if __name__ == "__main__":
    main()