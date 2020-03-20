"""This is the command-line program for cosmic ray.

Here we manage command-line parsing and launching of the internal machinery that does mutation testing.
"""
import json
import logging
import os
import signal
import subprocess
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from pathlib import Path

import click
from exit_codes import ExitCode

import cosmic_ray.commands
import cosmic_ray.modules
import cosmic_ray.mutating
import cosmic_ray.plugins
import cosmic_ray.testing
from cosmic_ray.config import load_config, serialize_config
from cosmic_ray.mutating import apply_mutation
from cosmic_ray.progress import report_progress
from cosmic_ray.version import __version__
from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import TestOutcome, WorkItem, WorkItemJsonEncoder

log = logging.getLogger()


@click.group()
@click.option('--verbosity',
              default='WARNING',
              help="The logging level to use.",
              type=click.Choice(['CRITICAL', 'DEBUG', 'ERROR', 'FATAL', 'INFO', 'WARNING'],
                                case_sensitive=True))
@click.version_option(version=__version__)
def cli(verbosity):
    "Mutation testing for Python3"
    logging_level = getattr(logging, verbosity)
    logging.basicConfig(level=logging_level)


@cli.command()
@click.argument('config_file', type=click.File('wt'))
def new_config(config_file):
    """Create a new config file.
    """
    cfg = cosmic_ray.commands.new_config()
    config_str = serialize_config(cfg)
    config_file.write(config_str)
    sys.exit(ExitCode.OK)


click.argument()
@cli.command()
@click.argument('config_file')
@click.argument('session_file',
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

    modules = cosmic_ray.modules.find_modules(Path(cfg['module-path']))
    modules = cosmic_ray.modules.filter_paths(
        modules, cfg.get('exclude-modules', ()))

    if log.isEnabledFor(logging.INFO):
        log.info('Modules discovered:')
        per_dir = defaultdict(list)
        for m in modules:
            per_dir[m.parent].append(m.name)
        for directory, files in per_dir.items():
            log.info(' - %s: %s', directory, ', '.join(sorted(files)))

    with use_db(session_file) as database:
        cosmic_ray.commands.init(modules, database, cfg)

    sys.exit(ExitCode.OK)


@cli.command()
@click.argument('session_file',
                # help="The database containing the config to be displayed."
                )
def config(session_file):
    """Show the configuration for a session."""
    with use_db(session_file) as database:
        cfg = database.get_config()
        print(serialize_config(cfg))

    sys.exit(ExitCode.OK)


@cli.command(name='exec')
@click.argument('session_file')
def handle_exec(session_file):
    """Perform the remaining work to be done in the specified session.
    This requires that the rest of your mutation testing
    infrastructure (e.g. worker processes) are already running.
    """
    with use_db(session_file, mode=WorkDB.Mode.open) as work_db:
        cosmic_ray.commands.execute(work_db)
    sys.exit(ExitCode.OK)


@cli.command()
@click.argument('session_file')
@click.option(
    '--force', 'force', flag_value=True,
    default=False,
    help="Force write over baseline session file if this file was already created by a previous run.")
@click.option(
    '--report', 'dump_report', flag_value=True,
    default=False,
    help="Print the report result of this baseline run. If the job has failed, jobs's outputs will be displayed.")
def baseline(session_file, force, dump_report):
    """Runs a baseline execution that executes the test suite over unmutated code.

    Exits with 0 if the job has exited normally, otherwise 1.
    """
    session_file = Path(session_file)

    baseline_session_file = session_file.parent / '{}.baseline{}'.format(
        session_file.stem, session_file.suffix)

    # Find arbitrary work-item in input session that we can copy.
    with use_db(session_file) as db:  # type: WorkDB
        try:
            template = next(iter(db.work_items))
        except StopIteration:
            log.error('No work items in session')
            sys.exit(ExitCode.DATA_ERR)

        cfg = db.get_config()

    if force:
        try:
            os.unlink(baseline_session_file)
        except OSError:
            pass

    # Copy input work-item, but tell it to use the no-op operator. Create a new
    # session containing only this work-item and execute this new session.
    with use_db(baseline_session_file, mode=WorkDB.Mode.create) as db:
        db.set_config(cfg)

        db.add_work_item(
            WorkItem(
                module_path=template.module_path,
                operator_name='core/NoOp',
                occurrence=0,
                start_pos=template.start_pos,
                end_pos=template.end_pos,
                job_id=template.job_id))

        # Run the single-entry session.
        cosmic_ray.commands.execute(db)

        result = next(db.results)[1]  # type: WorkResult
        if result.test_outcome == TestOutcome.KILLED:
            if dump_report:
                print("Execution with no mutation gives those following errors:")
                for line in result.output.split('\n'):
                    print("  >>>", line)
            sys.exit(1)
        else:
            if dump_report:
                print("Execution with no mutation works fine:")
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
    with use_db(session_file, WorkDB.Mode.open) as database:
        for work_item, result in database.completed_work_items:
            print(json.dumps((work_item, result), cls=WorkItemJsonEncoder))
        for work_item in database.pending_work_items:
            print(json.dumps((work_item, None), cls=WorkItemJsonEncoder))

    sys.exit(ExitCode.OK)


@cli.command()
def operators():
    """List the available operator plugins."""
    print('\n'.join(cosmic_ray.plugins.operator_names()))

    sys.exit(ExitCode.OK)


@cli.command()
def execution_engines():
    """List the available execution-engine plugins."""
    print('\n'.join(cosmic_ray.plugins.execution_engine_names()))

    sys.exit(ExitCode.OK)


@cli.command()
@click.argument('module_path')
@click.argument('operator')
@click.argument('occurrence', type=int)
@click.option('--python-version', help="Python major.minor version (e.g. 3.6) of the code being mutated.")
def apply(module_path, operator, occurrence, python_version):
    """Apply the specified mutation to the files on disk. This is primarily a debugging tool.
    """

    if python_version is None:
        python_version = "{}.{}".format(sys.version_info.major,
                                        sys.version_info.minor)

    apply_mutation(
        Path(module_path),
        cosmic_ray.plugins.get_operator(operator)(python_version),
        occurrence)

    sys.exit(ExitCode.OK)


@cli.command()
@click.argument('module_path')
@click.argument('operator')
@click.argument('occurrence', type=int)
@click.argument('config_file', required=False, default=None)
@click.option('--keep-stdout', default=False, flag_value=True, help='Do not squelch output.')
def worker(module_path, operator, occurrence, config_file, keep_stdout):
    """Run a worker process which performs a single mutation and test run.
    Each worker does a minimal, isolated chunk of work: it mutates the
    <occurrence>-th instance of <operator> in <module-path>, runs the test
    suite defined in the configuration, prints the results, and exits.

    Normally you won't run this directly. Rather, it will be launched
    by an execution engine. However, it can be useful to run this on
    its own for testing and debugging purposes.
    """
    cfg = load_config(config_file)

    with open(os.devnull, 'w') as devnull:
        with redirect_stdout(sys.stdout if keep_stdout else devnull):
            work_item = cosmic_ray.mutating.mutate_and_test(
                Path(module_path),
                cfg.python_version, operator,
                occurrence,
                cfg.test_command,
                None)

    sys.stdout.write(json.dumps(work_item, cls=WorkItemJsonEncoder))

    sys.exit(ExitCode.OK)


_SIGNAL_EXIT_CODE_BASE = 128


def main(argv=None):
    """ Invoke the cosmic ray evaluation.

    :param argv: the command line arguments
    """
    signal.signal(
        signal.SIGINT,
        lambda *args: sys.exit(_SIGNAL_EXIT_CODE_BASE + signal.SIGINT))

    if hasattr(signal, 'SIGINFO'):
        signal.signal(
            getattr(signal, 'SIGINFO'),
            lambda *args: report_progress(sys.stderr))

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
        print('Error in subprocess', file=sys.stderr)
        print(exc, file=sys.stderr)
        return exc.returncode
    except SystemExit as exc:
        # We intercept this here so that main() is testable.
        return exc.code


if __name__ == '__main__':
    sys.exit(main())
