"""This is the command-line program for cosmic ray.

Here we manage command-line parsing and launching of the internal
machinery that does mutation testing.
"""
import itertools
import json
import logging
import os
import pprint
import subprocess
import sys

import docopt_subcommands as dsc

import cosmic_ray.commands
from cosmic_ray.config import ConfigError, get_db_name, load_config
import cosmic_ray.counting
import cosmic_ray.modules
import cosmic_ray.worker
from cosmic_ray.testing.test_runner import TestOutcome
from cosmic_ray.timing import Timer
from cosmic_ray.util import redirect_stdout
from cosmic_ray.work_db import use_db, WorkDB


LOG = logging.getLogger()


@dsc.command()
def handle_baseline(args):
    """usage: cosmic-ray baseline [<config-file>]

Run an un-mutated baseline of a module using the tests specified in the config.
This is largely like running a "worker" process, with the difference that a
baseline run doesn't mutate the code.
    """
    sys.path.insert(0, '')

    config = load_config(args.get('<config-file>'))

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
def handle_init(args):
    """usage: cosmic-ray init [<config-file>]

Initialize a mutation testing run. The primarily creates a database of "work to
be done" which describes all of the mutations and test runs that need to be
executed for a full mutation testing run. The testing run will mutate
<top-module> (and submodules) using the tests in <test-dir>. This doesn't
actually run any tests. Instead, it scans the modules-under-test and simply
generates the work order which can be executed with other commands.

The session-name argument identifies the run you're creating. Its most
important role is that it's used to name the database file.
    """
    # This lets us import modules from the current directory. Should probably
    # be optional, and needs to also be applied to workers!
    sys.path.insert(0, '')

    config = load_config(args.get('<config-file>'))

    if 'timeout' in config:
        timeout = float(config['timeout'])
    elif 'baseline' in config:
        baseline_mult = float(config['baseline'])
        assert baseline_mult is not None # TODO: Should not be assertion
        command = 'cosmic-ray baseline {}'.format(
            args['<config-file>'])

        # We run the baseline in a subprocess to more closely emulate the
        # runtime of a worker subprocess.
        with Timer() as t:
            subprocess.check_call(command.split())

        timeout = baseline_mult * t.elapsed.total_seconds()
    else:
        raise ConfigError(
            "Config must specify either baseline or timeout")

    LOG.info('timeout = %f seconds', timeout)

    modules = set(
        cosmic_ray.modules.find_modules(
            cosmic_ray.modules.fixup_module_name(config['module']),
            config.get('exclude-modules', None)))

    LOG.info('Modules discovered: %s', [m.__name__ for m in modules])

    db_name = get_db_name(config['session'])

    with use_db(db_name) as db:
        cosmic_ray.commands.init(
            modules,
            db,
            config['test-runner']['name'],
            config['test-runner']['args'],
            timeout)


@dsc.command()
def handle_exec(args):
    """usage: cosmic-ray exec [<config-file>]

Perform the remaining work to be done in the specified session. This requires
that the rest of your mutation testing infrastructure (e.g. worker processes)
are already running.
    """

    config = load_config(args.get('<config-file>'))
    cosmic_ray.commands.execute(config)


@dsc.command()
def handle_dump(args):
    """usage: cosmic-ray dump <session-file>

JSON dump of session data.
    """
    db_name = get_db_name(args['<session-file>'])

    with use_db(db_name, WorkDB.Mode.open) as db:
        for record in db.work_records:
            print(json.dumps(record))


@dsc.command()
def handle_counts(configuration):
    """usage: {program} counts [options] [--exclude-modules=P ...] <top-module>

Count the number of tests that would be run for a given testing configuration.
This is mostly useful for estimating run times and keeping track of testing
statistics.

options:
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation
"""
    sys.path.insert(0, '')

    modules = cosmic_ray.modules.find_modules(
        cosmic_ray.modules.fixup_module_name(configuration['<top-module>']),
        configuration['--exclude-modules'])

    operators = cosmic_ray.plugins.operator_names()

    counts = cosmic_ray.counting.count_mutants(modules, operators)

    print('[Counts]')
    pprint.pprint(counts)
    print('\n[Total test runs]\n',
          sum(itertools.chain(
              *(d.values() for d in counts.values()))))


@dsc.command()
def handle_test_runners(config):
    """usage: {program} test-runners

List the available test-runner plugins.
"""
    print('\n'.join(cosmic_ray.plugins.test_runner_names()))
    return 0


@dsc.command()
def handle_operators(config):
    """usage: {program} operators

List the available operator plugins.
"""
    print('\n'.join(cosmic_ray.plugins.operator_names()))
    return 0


@dsc.command()
def handle_worker(args):
    """usage: {program} worker [options] <module> <operator> <occurrence> [<config-file>]

Run a worker process which performs a single mutation and test run. Each
worker does a minimal, isolated chunk of work: it mutates the <occurence>-th
instance of <operator> in <module>, runs the test suite defined by
<test-runner> and <test-args>, prints the results, and exits.

Normally you won't run this directly. Rather, it will be launched by celery
worker tasks.

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

    with open(os.devnull, 'w') as devnull,\
        redirect_stdout(sys.stdout if args['--keep-stdout'] else devnull):
        work_record = cosmic_ray.worker.worker(
            args['<module>'],
            operator,
            int(args['<occurrence>']),
            test_runner)

    sys.stdout.write(
        json.dumps(work_record))


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
    if config['--verbose']:
        logging.basicConfig(level=logging.INFO)


def main(argv=None):
    dsc.main(
        'cosmic-ray',
        'cosmic-ray v.2',
        argv=argv,
        doc_template=DOC_TEMPLATE,
        common_option_handler=common_option_handler)


if __name__ == '__main__':
    main()
