"""This is the command-line program for cosmic ray.

Here we manage command-line parsing and launching of the internal machinery that does mutation testing.
"""
import asyncio
import dataclasses
import json
import logging
import os
import signal
import subprocess
import sys
from collections import defaultdict
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
import tempfile

import click
from exit_codes import ExitCode
from rich.logging import RichHandler

import cosmic_ray.commands
import cosmic_ray.modules
import cosmic_ray.mutating
import cosmic_ray.plugins
import cosmic_ray.testing
import cosmic_ray.distribution.http
from cosmic_ray.config import load_config, serialize_config
from cosmic_ray.mutating import apply_mutation
from cosmic_ray.progress import report_progress
from cosmic_ray.version import __version__
from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.work_item import TestOutcome, WorkItem

log = logging.getLogger()


@click.group()
@click.option(
    "--verbosity",
    default="WARNING",
    help="The logging level to use.",
    type=click.Choice(["CRITICAL", "DEBUG", "ERROR", "FATAL", "INFO", "WARNING"], case_sensitive=True),
)
@click.version_option(version=__version__)
def cli(verbosity):
    "Mutation testing for Python3"
    logging_level = getattr(logging, verbosity)
    logging.basicConfig(level=logging_level, handlers=[RichHandler()])

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@cli.command()
@click.argument("config_file", type=click.File("wt"))
def new_config(config_file):
    """Create a new config file."""
    cfg = cosmic_ray.commands.new_config()
    config_str = serialize_config(cfg)
    config_file.write(config_str)
    sys.exit(ExitCode.OK)


click.argument()


@cli.command()
@click.argument("config_file")
@click.argument(
    "session_file",
    # help="The filename for the database in which the work order will be stored."
)
def init(config_file, session_file):
    """Initialize a mutation testing session from a configuration. This
    primarily creates a session - a database of "work to be done" -
    which describes all of the mutations and test runs that need to be
    executed for a full mutation testing run. The configuration
    specifies the top-level module to mutate, the tests to run, and how
    to run them.

    This command doesn't actually run any tests. Instead, it scans the
    modules-under-test and simply generates the work order which can be
    executed with other commands.
    """
    cfg = load_config(config_file)

    modules = cosmic_ray.modules.find_modules(Path(cfg["module-path"]))
    modules = cosmic_ray.modules.filter_paths(modules, cfg.get("exclude-modules", ()))

    if log.isEnabledFor(logging.INFO):
        log.info("Modules discovered:")
        per_dir = defaultdict(list)
        for m in modules:
            per_dir[m.parent].append(m.name)
        for directory, files in per_dir.items():
            log.info(" - %s: %s", directory, ", ".join(sorted(files)))

    with use_db(session_file) as database:
        cosmic_ray.commands.init(modules, database)

    sys.exit(ExitCode.OK)


@cli.command(name="exec")
@click.argument("config_file")
@click.argument("session_file")
def handle_exec(config_file, session_file):
    """Perform the remaining work to be done in the specified session.
    This requires that the rest of your mutation testing
    infrastructure (e.g. worker processes) are already running.
    """
    cfg = load_config(config_file)

    with use_db(session_file, mode=WorkDB.Mode.open) as work_db:
        cosmic_ray.commands.execute(work_db, cfg)
    sys.exit(ExitCode.OK)


@cli.command()
@click.argument("config_file")
@click.option(
    "--session-file",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Path to session file. If not provided, a temp file is used.",
)
def baseline(config_file, session_file):
    """Runs a baseline execution that executes the test suite over unmutated code.

    If ``--session-file`` is provided, the session used for baselining is stored in that file. Otherwise,
    the session is stored in a temporary file which is deleted after the baselining.

    Exits with 0 if the job has exited normally, otherwise 1.
    """
    cfg = load_config(config_file)

    @contextmanager
    def path_or_temp(path):
        if path is None:
            with tempfile.TemporaryDirectory() as tmpdir:
                yield Path(tmpdir) / "session.sqlite"
        else:
            yield path

    with path_or_temp(session_file) as session_path:
        with use_db(session_path, mode=WorkDB.Mode.create) as db:
            db.clear()
            db.add_work_item(
                WorkItem(
                    mutations=[],
                    job_id="baseline",
                )
            )

            # Run the single-entry session.
            cosmic_ray.commands.execute(db, cfg)

            result = next(db.results)[1]
            if result.test_outcome == TestOutcome.KILLED:
                message = ["Baseline failed. Execution with no mutation gives those following errors:"]
                for line in result.output.split("\n"):
                    message.append("  >>> {}".format(line))
                log.error("\n".join(message))
                sys.exit(1)
            else:
                log.info("Baseline passed. Execution with no mutation works fine.")
                sys.exit(ExitCode.OK)


@cli.command()
@click.argument("session_file")
def dump(session_file):
    """JSON dump of session data. This output is typically run through other
    programs to produce reports.

    Each line of output is a list with two elements: a WorkItem and a
    WorkResult, both JSON-serialized. The WorkResult can be null, indicating a
    WorkItem with no results.
    """

    def item_to_dict(work_item):
        d = dataclasses.asdict(work_item)
        for m in d["mutations"]:
            m["module_path"] = str(m["module_path"])
        return d

    def result_to_dict(result):
        d = dataclasses.asdict(result)
        d["worker_outcome"] = d["worker_outcome"].value
        d["test_outcome"] = d["test_outcome"].value
        return d

    with use_db(session_file, WorkDB.Mode.open) as database:
        for work_item, result in database.completed_work_items:
            print(json.dumps((item_to_dict(work_item), result_to_dict(result))))
        for work_item in database.pending_work_items:
            print(json.dumps((item_to_dict(work_item), None)))

    sys.exit(ExitCode.OK)


@cli.command()
def operators():
    """List the available operator plugins."""
    print("\n".join(cosmic_ray.plugins.operator_names()))

    sys.exit(ExitCode.OK)


@cli.command()
def distributors():
    """List the available distributor plugins."""
    print("\n".join(cosmic_ray.plugins.distributor_names()))

    sys.exit(ExitCode.OK)


@cli.command()
@click.argument("module_path")
@click.argument("operator")
@click.argument("occurrence", type=int)
def apply(module_path, operator, occurrence):
    """Apply the specified mutation to the files on disk. This is primarily a debugging tool."""

    apply_mutation(Path(module_path), cosmic_ray.plugins.get_operator(operator)(), occurrence)

    sys.exit(ExitCode.OK)


@cli.command()
@click.option("--port", type=int, default=None, help="The port on which to listen for requests")
@click.option("--path", default=None, help="Path to Unix domain socket on which to listen for requests")
def http_worker(port, path):
    """Run an HTTP worker for the 'http' distributor."""
    if (port is None) == (path is None):
        log.error("You must specify exactly one of --path or --port")
        sys.exit(ExitCode.USAGE)

    try:
        cosmic_ray.distribution.http.run_worker(port=port, path=path)
    except ValueError as exc:
        log.error(str(exc))
        sys.exit(ExitCode.DATA_ERR)

    sys.exit(ExitCode.OK)


@cli.command()
@click.argument("module_path")
@click.argument("operator")
@click.argument("occurrence", type=int)
@click.argument("test_command")
@click.option("--keep-stdout", default=False, flag_value=True, help="Do not squelch output.")
def mutate_and_test(module_path, operator, occurrence, test_command, keep_stdout):
    """Run a worker process which performs a single mutation and test run.
    Each worker does a minimal, isolated chunk of work: it mutates the
    <occurrence>-th instance of <operator> in <module-path>, runs the test
    suite defined in the configuration, prints the results, and exits.

    Normally you won't run this directly. Rather, it will be launched
    by an distributor. However, it can be useful to run this on
    its own for testing and debugging purposes.
    """
    with open(os.devnull, "w") as devnull:
        with redirect_stdout(sys.stdout if keep_stdout else devnull):
            work_result = asyncio.get_event_loop().run_until_complete(
                cosmic_ray.mutating.mutate_and_test(Path(module_path), operator, occurrence, test_command, None)
            )

    sys.stdout.write(json.dumps(dataclasses.asdict(work_result)))

    sys.exit(ExitCode.OK)


_SIGNAL_EXIT_CODE_BASE = 128


def main(argv=None):
    """Invoke the cosmic ray evaluation.

    :param argv: the command line arguments
    """
    signal.signal(signal.SIGINT, lambda *args: sys.exit(_SIGNAL_EXIT_CODE_BASE + signal.SIGINT))

    if hasattr(signal, "SIGINFO"):
        signal.signal(getattr(signal, "SIGINFO"), lambda *args: report_progress(sys.stderr))

    try:
        return cli(argv)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return ExitCode.NO_INPUT
    except PermissionError as exc:
        print(exc, file=sys.stderr)
        return ExitCode.NO_PERM
    except cosmic_ray.config.ConfigError as exc:
        print(repr(exc), file=sys.stderr)
        if exc.__cause__ is not None:
            print(exc.__cause__, file=sys.stderr)
        return ExitCode.CONFIG
    except subprocess.CalledProcessError as exc:
        print("Error in subprocess", file=sys.stderr)
        print(exc, file=sys.stderr)
        return exc.returncode
    except SystemExit as exc:
        # We intercept this here so that main() is testable.
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
