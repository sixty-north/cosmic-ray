"""This is the command-line program for cosmic ray.

Here we manage command-line parsing and launching of the internal
machinery that does mutation testing.
"""
import itertools
import json
import logging
import os
import pprint
import signal
import subprocess
import sys

import docopt
import docopt_subcommands as dsc

import cosmic_ray.commands
import cosmic_ray.counting
import cosmic_ray.modules
import cosmic_ray.plugins
import cosmic_ray.worker
from cosmic_ray.config import ConfigError, get_db_name, load_config
from cosmic_ray.testing.test_runner import TestOutcome
from cosmic_ray.timing import Timer
from cosmic_ray.util import redirect_stdout
from cosmic_ray.work_db import use_db, WorkDB

LOG = logging.getLogger()


@dsc.command()
def handle_baseline(args):
    """usage: cosmic-ray baseline <config-file>

Run an un-mutated baseline of the specific configuration. This is largely like
running a "worker" process, with the difference that a baseline run doesn't
mutate the code.

    """
    sys.path.insert(0, '')

    config = load_config(args['<config-file>'])

    test_runner = cosmic_ray.plugins.get_test_runner(
        config['test-runner']['name'],
        config['test-runner']['args'])

    work_record = test_runner()
    # note: test_runner() results are meant to represent
    # status codes when executed against mutants.
    # SURVIVED means that the test suite executed without any error
    # hence CR thinks the mutant survived. However when running the
    # baseline execution we don't have mutations and really want the
    # test suite to report PASS, hence the comparison below!
    if work_record.test_outcome != TestOutcome.SURVIVED:
        # baseline failed, print whatever was returned
        # from the test runner and exit
        LOG.error('baseline failed')
        print(''.join(work_record.data))
        sys.exit(2)


@dsc.command()
def handle_new_config(args):
    """usage: cosmic-ray new-config <config-file>

Create a new config file.
    """
    config = cosmic_ray.commands.new_config()
    with open(args['<config-file>'], mode='wt') as handle:
        handle.write(config)


@dsc.command()
def handle_init(args):
    """usage: cosmic-ray init <config-file> <session-file>

Initialize a mutation testing session from a configuration. This primarily
creates a session - a database of "work to be done" - which describes all of
the mutations and test runs that need to be executed for a full mutation
testing run. The configuration specifies the top-level module to mutate, the
tests to run, and how to run them.

This command doesn't actually run any tests. Instead, it scans the
modules-under-test and simply generates the work order which can be executed
with other commands.

The `session-file` is the filename for the database in which the work order
will be stored.
    """
    # This lets us import modules from the current directory. Should probably
    # be optional, and needs to also be applied to workers!
    sys.path.insert(0, '')

    config_file = args['<config-file>']

    if not os.path.exists(config_file):
        handle_new_config(args)

    config = load_config(config_file)

    if 'timeout' in config:
        timeout = float(config['timeout'])
    elif 'baseline' in config:
        baseline_mult = float(config['baseline'])
        # TODO: Should not be assertion
        assert baseline_mult is not None
        command = 'cosmic-ray baseline {}'.format(
            args['<config-file>'])

        # We run the baseline in a subprocess to more closely emulate the
        # runtime of a worker subprocess.
        with Timer() as timer:
            subprocess.check_call(command.split())

        timeout = baseline_mult * timer.elapsed.total_seconds()
    else:
        raise ConfigError(
            "Config must specify either baseline or timeout")

    LOG.info('timeout = %f seconds', timeout)

    modules = set(
        cosmic_ray.modules.find_modules(
            cosmic_ray.modules.fixup_module_name(config['module']),
            config.get('exclude-modules', None)))

    LOG.info('Modules discovered: %s', [m.__name__ for m in modules])

    db_name = get_db_name(args['<session-file>'])

    with use_db(db_name) as database:
        cosmic_ray.commands.init(
            modules,
            database,
            config,
            timeout)


@dsc.command()
def handle_config(args):
    """usage: cosmic-ray config <session-file>

Show the configuration for in a session.
    """
    session_file = get_db_name(args['<session-file>'])
    with use_db(session_file) as database:
        config, _ = database.get_config()
        print(json.dumps(config))


@dsc.command()
def handle_exec(args):
    """usage: cosmic-ray exec <session-file>

Perform the remaining work to be done in the specified session. This requires
that the rest of your mutation testing infrastructure (e.g. worker processes)
are already running.
    """

    session_file = get_db_name(
        args.get('<session-file>'))
    cosmic_ray.commands.execute(session_file)


@dsc.command()
def handle_dump(args):
    """usage: cosmic-ray dump <session-file>

JSON dump of session data. This output is typically run through other programs
to produce reports.
    """
    session_file = get_db_name(args['<session-file>'])

    with use_db(session_file, WorkDB.Mode.open) as database:
        for record in database.work_records:
            print(json.dumps(record))


@dsc.command()
def handle_counts(args):
    """usage: {program} counts <config-file>

Count the number of tests that would be run for a given testing configuration.
This is mostly useful for estimating run times and keeping track of testing
statistics.
"""
    config = load_config(args['<config-file>'])

    sys.path.insert(0, '')

    modules = cosmic_ray.modules.find_modules(
        cosmic_ray.modules.fixup_module_name(config['module']),
        config.get('exclude-modules', []))

    operators = cosmic_ray.plugins.operator_names()

    counts = cosmic_ray.counting.count_mutants(modules, operators)

    print('[Counts]')
    pprint.pprint(counts)
    print('\n[Total test runs]\n',
          sum(itertools.chain(
              *(d.values() for d in counts.values()))))


@dsc.command()
def handle_test_runners(config):  # pylint: disable=unused-argument
    """usage: {program} test-runners

List the available test-runner plugins.
"""
    print('\n'.join(cosmic_ray.plugins.test_runner_names()))
    return 0


@dsc.command()
def handle_operators(config):  # pylint: disable=unused-argument
    """usage: {program} operators

List the available operator plugins.
"""
    print('\n'.join(cosmic_ray.plugins.operator_names()))
    return 0


@dsc.command()
def handle_worker(args):
    """usage: {program} worker \
    [options] <module> <operator> <occurrence> [<config-file>]

Run a worker process which performs a single mutation and test run. Each worker
does a minimal, isolated chunk of work: it mutates the <occurence>-th instance
of <operator> in <module>, runs the test suite defined in the configuration,
prints the results, and exits.

Normally you won't run this directly. Rather, it will be launched by an
execution engine. However, it can be useful to run this on its own for testing
and debugging purposes.

options:
  --keep-stdout       Do not squelch stdout

    """
    config = load_config(args.get('<config-file>'))

    if config.get('local-imports', True):
        sys.path.insert(0, '')

    operator = cosmic_ray.plugins.get_operator(args['<operator>'])
    test_runner = cosmic_ray.plugins.get_test_runner(
        config['test-runner']['name'],
        config['test-runner']['args'])

    with open(os.devnull, 'w') as devnull:
        with redirect_stdout(sys.stdout if args['--keep-stdout'] else devnull):
            work_record = cosmic_ray.worker.worker(
                args['<module>'],
                operator,
                int(args['<occurrence>']),
                test_runner)

    sys.stdout.write(json.dumps(work_record))


DOC_TEMPLATE = """{program}

Usage: {program} [options] <command> [<args> ...]

Options:
  -h --help     Show this screen.
  -v --verbose  Use verbose logging

Available commands:
  {available_commands}

See '{program} help <command>' for help on specific commands.
"""


def common_option_handler(config):
    """Add verbose mode.

    :param config: holds the configuration values
    """
    if config['--verbose']:
        logging.basicConfig(level=logging.INFO)


def main(argv=None):
    """ Invoke the cosmic ray evaluation.

    :param argv: the command line arguments
    """
    signal.signal(signal.SIGINT,
                  lambda *args: sys.exit(0))

    try:
        dsc.main(
            'cosmic-ray',
            'cosmic-ray v.2',
            argv=argv,
            doc_template=DOC_TEMPLATE,
            common_option_handler=common_option_handler)
    except docopt.DocoptExit as exc:
        exc.code = os.EX_USAGE
        raise


if __name__ == '__main__':
    main()
