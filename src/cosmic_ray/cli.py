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

import docopt
import docopt_subcommands
from docopt_subcommands.subcommands import Subcommands
from exit_codes import ExitCode

import cosmic_ray.commands
import cosmic_ray.modules
import cosmic_ray.plugins
import cosmic_ray.testing
import cosmic_ray.worker
from cosmic_ray.config import load_config, serialize_config
from cosmic_ray.mutating import apply_mutation
from cosmic_ray.progress import report_progress
from cosmic_ray.version import __version__
from cosmic_ray.work_db import WorkDB, use_db
from cosmic_ray.work_item import WorkItem, WorkItemJsonEncoder, WorkResult, \
    TestOutcome

log = logging.getLogger()


DOC_TEMPLATE = """{program}

Usage: {program} [options] <command> [<args> ...]

Options:
  -h --help           Show this screen.
  --version           Show the program version.
  -v --verbosity=LEVEL  Use verbose output [default: WARNING]

Available commands:
  {available_commands}

See '{program} <command> -h' for help on specific commands.
"""


class CosmicRaySubcommands(Subcommands):
    "Subcommand handler."

    def _precommand_option_handler(self, config):
        verbosity_level = getattr(logging, config.get('--verbosity', 'WARNING'))

        logging.basicConfig(
            level=verbosity_level,
            format='%(asctime)s %(name)s %(levelname)s %(message)s')

        return super()._precommand_option_handler(config)


dsc = CosmicRaySubcommands(
    program='cosmic-ray',
    version='Cosmic Ray {}'.format(__version__),
    doc_template=DOC_TEMPLATE)


@dsc.command()
def handle_new_config(args):
    """usage: cosmic-ray new-config <config-file>

    Create a new config file.
    """
    config = cosmic_ray.commands.new_config()
    config_str = serialize_config(config)
    with open(args['<config-file>'], mode='wt') as handle:
        handle.write(config_str)

    return ExitCode.OK


@dsc.command()
def handle_init(args):
    """usage: cosmic-ray init <config-file> <session-file>

    Initialize a mutation testing session from a configuration. This
    primarily creates a session - a database of "work to be done" -
    which describes all of the mutations and test runs that need to be
    executed for a full mutation testing run. The configuration
    specifies the top-level module to mutate, the tests to run, and how
    to run them.

    This command doesn't actually run any tests. Instead, it scans the
    modules-under-test and simply generates the work order which can be
    executed with other commands.

    The `session-file` is the filename for the database in which the
    work order will be stored.
    """
    config_file = args['<config-file>']

    config = load_config(config_file)

    modules = cosmic_ray.modules.find_modules(Path(config['module-path']))
    modules = cosmic_ray.modules.filter_paths(modules, config.get('exclude-modules', ()))

    if log.isEnabledFor(logging.INFO):
        log.info('Modules discovered:')
        per_dir = defaultdict(list)
        for m in modules:
            per_dir[m.parent].append(m.name)
        for dir, files in per_dir.items():
            log.info(' - %s: %s', dir, ', '.join(sorted(files)))

    db_name = args['<session-file>']

    with use_db(db_name) as database:
        cosmic_ray.commands.init(modules, database, config)

    return ExitCode.OK


@dsc.command()
def handle_config(args):
    """usage: cosmic-ray config <session-file>

    Show the configuration for in a session.
    """
    session_file = args['<session-file>']
    with use_db(session_file) as database:
        config = database.get_config()
        print(serialize_config(config))

    return ExitCode.OK


@dsc.command()
def handle_exec(args):
    """usage: cosmic-ray exec <session-file>

    Perform the remaining work to be done in the specified session.
    This requires that the rest of your mutation testing
    infrastructure (e.g. worker processes) are already running.
    """
    session_file = args.get('<session-file>')
    with use_db(session_file, mode=WorkDB.Mode.open) as work_db:
        cosmic_ray.commands.execute(work_db)
    return ExitCode.OK


@dsc.command()
def handle_baseline(args):
    """usage: cosmic-ray baseline [--force] [--report] <session-file>

    Runs a baseline execution that executes the test suite over
    unmutated code.

    options:
      --force      Force write over baseline session file
                   if this file was already created by a previous
                   run.
      --report     Print the report result of this baseline run.
                   If the job has failed, jobs's outputs will be
                   displayed.

    return code:
        0 if the job has exited normally, else 1.

    """
    session_file = Path(args.get('<session-file>'))
    force = args.get('--force', False)
    dump_report = args.get('--report', False)

    baseline_session_file = session_file.parent / '{}.baseline{}'.format(
        session_file.stem, session_file.suffix)

    # Find arbitrary work-item in input session that we can copy.
    with use_db(session_file) as db:  # type: WorkDB
        try:
            template = next(iter(db.work_items))
        except StopIteration:
            log.error('No work items in session')
            return ExitCode.DATA_ERR

        config = db.get_config()

    if force:
        try:
            os.unlink(baseline_session_file)
        except OSError:
            pass

    # Copy input work-item, but tell it to use the no-op operator. Create a new
    # session containing only this work-item and execute this new session.
    with use_db(baseline_session_file, mode=WorkDB.Mode.create) as db:
        db.set_config(config)

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
            return 1
        else:
            if dump_report:
                print("Execution with no mutation works fine:")
            return ExitCode.OK


@dsc.command()
def handle_dump(args):
    """usage: cosmic-ray dump <session-file>

    JSON dump of session data. This output is typically run through other
    programs to produce reports.

    Each line of output is a list with two elements: a WorkItem and a
    WorkResult, both JSON-serialized. The WorkResult can be null, indicating a
    WorkItem with no results.
    """
    session_file = args['<session-file>']

    with use_db(session_file, WorkDB.Mode.open) as database:
        for work_item, result in database.completed_work_items:
            print(json.dumps((work_item, result), cls=WorkItemJsonEncoder))
        for work_item in database.pending_work_items:
            print(json.dumps((work_item, None), cls=WorkItemJsonEncoder))

    return ExitCode.OK


@dsc.command()
def handle_operators(args):
    """usage: {program} operators

    List the available operator plugins.
    """
    assert args
    print('\n'.join(cosmic_ray.plugins.operator_names()))

    return ExitCode.OK


@dsc.command()
def handle_execution_engines(args):
    """usage: {program} execution-engines

    List the available execution-engine plugins.
    """
    assert args
    print('\n'.join(cosmic_ray.plugins.execution_engine_names()))

    return ExitCode.OK


@dsc.command()
def handle_apply(args):
    """usage: {program} apply <module-path> <operator> <occurrence>

    Apply the specified mutation to the files on disk. This is primarily a debugging
    tool.

    options:
      --python-version=VERSION  Python major.minor version (e.g. 3.6) of the code being mutated.
    """

    python_version = args['--python-version']
    if python_version is None:
        python_version = "{}.{}".format(sys.version_info.major,
                                        sys.version_info.minor)

    apply_mutation(
        Path(args['<module-path>']),
        cosmic_ray.plugins.get_operator(args['<operator>'])(python_version),
        int(args['<occurrence>']))

    return ExitCode.OK


@dsc.command()
def handle_worker(args):
    """usage: {program} worker [options] <module-path> <operator> <occurrence> [<config-file>]

    Run a worker process which performs a single mutation and test run.
    Each worker does a minimal, isolated chunk of work: it mutates the
    <occurrence>-th instance of <operator> in <module-path>, runs the test
    suite defined in the configuration, prints the results, and exits.

    Normally you won't run this directly. Rather, it will be launched
    by an execution engine. However, it can be useful to run this on
    its own for testing and debugging purposes.

    options:
      --keep-stdout             Do not squelch stdout

    """
    config = load_config(args.get('<config-file>'))

    with open(os.devnull, 'w') as devnull:
        with redirect_stdout(sys.stdout if args['--keep-stdout'] else devnull):
            work_item = cosmic_ray.worker.worker(
                Path(args['<module-path>']),
                config.python_version, args['<operator>'],
                int(args['<occurrence>']),
                config.test_command,
                None)

    sys.stdout.write(json.dumps(work_item, cls=WorkItemJsonEncoder))

    return ExitCode.OK


DOC_TEMPLATE = """{program}

Usage: {program} [options] <command> [<args> ...]

Options:
  -h --help     Show this screen.
  -v --verbose  Use verbose logging

Available commands:
  {available_commands}

See '{program} help <command>' for help on specific commands.
"""


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
        return docopt_subcommands.main(
            commands=dsc,
            argv=argv,
            doc_template=DOC_TEMPLATE,
            exit_at_end=False)
    except docopt.DocoptExit as exc:
        print(exc, file=sys.stderr)
        return ExitCode.USAGE
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


if __name__ == '__main__':
    sys.exit(main())
