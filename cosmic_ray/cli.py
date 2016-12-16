"""This is the command-line program for cosmic ray.

Here we manage command-line parsing and launching of the internal
machinery that does mutation testing.
"""
import itertools
import json
import logging
import os
import pprint
import sys

import docopt
import transducer.eager
from transducer.functional import compose
import transducer.lazy
from transducer.transducers import filtering, mapping

import cosmic_ray.commands
import cosmic_ray.counting
import cosmic_ray.modules
import cosmic_ray.json_util
import cosmic_ray.worker
from cosmic_ray.timing import Timer
from cosmic_ray.util import redirect_stdout
from cosmic_ray.work_db import use_db, WorkDB
from cosmic_ray.testing.test_runner import Outcome


LOG = logging.getLogger()

REMOVE_COMMENTS = mapping(lambda x: x.split('#')[0])
REMOVE_WHITESPACE = mapping(str.strip)
NON_EMPTY = filtering(bool)
CONFIG_FILE_PARSER = compose(REMOVE_COMMENTS,
                             REMOVE_WHITESPACE,
                             NON_EMPTY)


def _load_file(config_file):
    """Read configuration from a file.

    This reads `config_file`, yielding each non-empty line with
    whitespace and comments stripped off.
    """
    with open(config_file, 'rt', encoding='utf-8') as f:
        yield from transducer.lazy.transduce(CONFIG_FILE_PARSER, f)


def handle_help(config):
    """usage: cosmic-ray help [<command>]

Get the top-level help, or help for <command> if specified.
"""
    command = config['<command>']
    if not command:
        options = OPTIONS
    elif command not in COMMAND_HANDLER_MAP:
        LOG.error('"%s" is not a valid cosmic-ray command', command)
        options = OPTIONS
    else:
        options = COMMAND_HANDLER_MAP[command].__doc__

    return docopt.docopt(options,
                         ['--help'],
                         version='cosmic-ray v.2')


def handle_load(config):
    """usage: cosmic-ray load <config-file>

Load a command configuration from <config-file> and run it.

A "command configuration" is simply a command-line invocation for cosmic-ray,
where each token of the command is on a separate line.
    """
    filename = config['<config-file>']
    argv = _load_file(filename)
    return main(argv=list(argv))


def handle_baseline(configuration):
    """usage: cosmic-ray baseline [options] <top-module> [-- <test-args> ...]

Run an un-mutated baseline of <top-module> using the tests in <test-dir>.
This is largely like running a "worker" process, with the difference
that a baseline run doesn't mutate the code.

options:
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
"""
    sys.path.insert(0, '')
    test_runner = cosmic_ray.plugins.get_test_runner(
        configuration['--test-runner'],
        configuration['<test-args>']
    )

    result = test_runner()
    # note: test_runner() results are meant to represent
    # status codes when executed against mutants.
    # SURVIVED means that the test suite executed without any error
    # hence CR thinks the mutant survived. However when running the
    # baseline execution we don't have mutations and really want the
    # test suite to report PASS, hence the comparison below!
    if result[0] != Outcome.SURVIVED:
        # baseline failed, print whatever was returned
        # from the test runner and exit
        LOG.error('baseline failed')
        print(''.join(result[1]))
        sys.exit(2)


def _get_db_name(session_name):
    if session_name.endswith('.json'):
        return session_name
    else:
        return '{}.json'.format(session_name)


def handle_init(configuration):
    """usage: cosmic-ray init [options] [--exclude-modules=P ...] (--timeout=T | --baseline=M) <session-name> <top-module> [-- <test-args> ...]

Initialize a mutation testing run. The primarily creates a database of "work to
be done" which describes all of the mutations and test runs that need to be
executed for a full mutation testing run. The testing run will mutate
<top-module> (and submodules) using the tests in <test-dir>. This doesn't
actually run any tests. Instead, it scans the modules-under-test and simply
generates the work order which can be executed with other commands.

The session-name argument identifies the run you're creating. Its most
important role is that it's used to name the database file.

options:
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation
    """
    # This lets us import modules from the current directory. Should probably
    # be optional, and needs to also be applied to workers!
    sys.path.insert(0, '')

    if configuration['--timeout'] is not None:
        timeout = float(configuration['--timeout'])
    else:
        baseline_mult = float(configuration['--baseline'])
        assert baseline_mult is not None
        with Timer() as t:
            handle_baseline(configuration)
        timeout = baseline_mult * t.elapsed.total_seconds()

    LOG.info('timeout = %f seconds', timeout)

    modules = set(
        cosmic_ray.modules.find_modules(
            cosmic_ray.modules.fixup_module_name(configuration['<top-module>']),
            configuration['--exclude-modules']))

    LOG.info('Modules discovered: %s', [m.__name__ for m in modules])

    db_name = _get_db_name(configuration['<session-name>'])

    with use_db(db_name) as db:
        cosmic_ray.commands.init(
            modules,
            db,
            configuration['--test-runner'],
            configuration['<test-args>'],
            timeout)


def handle_exec(configuration):
    """usage: cosmic-ray exec [--dist] <session-name>

Perform the remaining work to be done in the specified session. This requires
that the rest of your mutation testing infrastructure (e.g. worker processes)
are already running.

options:
    --dist  Distribute tests to remote workers
    """
    db_name = _get_db_name(configuration['<session-name>'])
    dist = configuration['--dist']

    with use_db(db_name, mode=WorkDB.Mode.open) as db:
        cosmic_ray.commands.execute(db, dist)


def handle_run(configuration):
    """usage: cosmic-ray run [options] [--dist] [--exclude-modules=P ...] (--timeout=T | --baseline=M) <session-name> <top-module> [-- <test-args> ...]

This simply runs the "init" command followed by the "exec" command.

It's important to remember that "init" clears the session database, including
any results you may have already received. So DO NOT USE THIS COMMAND TO
CONTINUE EXECUTION OF AN INTERRUPTED SESSION! If you do this, you will lose any
existing results.

options:
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation

    """
    handle_init(configuration)
    handle_exec(configuration)


def handle_report(configuration):
    """usage: cosmic-ray report [--full-report] [--show-pending] <session-name>

Print a nicely formatted report of test results and some basic statistics.

options:
    --full-report  Show test output and mutation diff for killed mutants

    """
    db_name = _get_db_name(configuration['<session-name>'])
    show_pending = configuration['--show-pending']
    full_report = configuration['--full-report']

    with use_db(db_name, WorkDB.Mode.open) as db:
        for line in cosmic_ray.commands.create_report(db, show_pending, full_report):
            print(line)


def handle_survival_rate(configuration):
    """usage: cosmic-ray survival-rate <session-name>

Print the session's survival rate.
    """
    db_name = _get_db_name(configuration['<session-name>'])

    with use_db(db_name, WorkDB.Mode.open) as db:
        rate = cosmic_ray.commands.survival_rate(db)
        print('{:.2f}'.format(rate))


def handle_counts(configuration):
    """usage: cosmic-ray counts [options] [--exclude-modules=P ...] <top-module>

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


def handle_test_runners(config):
    """usage: cosmic-ray test-runners

List the available test-runner plugins.
"""
    print('\n'.join(cosmic_ray.plugins.test_runner_names()))
    return 0


def handle_operators(config):
    """usage: cosmic-ray operators

List the available operator plugins.
"""
    print('\n'.join(cosmic_ray.plugins.operator_names()))
    return 0


def handle_worker(config):
    """usage: cosmic-ray worker [options] <module> <operator> <occurrence> <test-runner> [-- <test-args> ...]

Run a worker process which performs a single mutation and test run. Each
worker does a minimal, isolated chunk of work: it mutates the <occurence>-th
instance of <operator> in <module>, runs the test suite defined by
<test-runner> and <test-args>, prints the results, and exits.

Normally you won't run this directly. Rather, it will be launched by celery
worker tasks.

options:
  --no-local-import   Disallow importing module from the current directory
  --keep-stdout       Do not squelch stdout
"""
    if not config['--no-local-import']:
        sys.path.insert(0, '')

    operator = cosmic_ray.plugins.get_operator(config['<operator>'])
    test_runner = cosmic_ray.plugins.get_test_runner(
        config['<test-runner>'],
        config['<test-args>'])

    with open(os.devnull, 'w') as devnull,\
        redirect_stdout(sys.stdout if config['--keep-stdout'] else devnull):
        result_type, data = cosmic_ray.worker.worker(
            config['<module>'],
            operator,
            int(config['<occurrence>']),
            test_runner)

    sys.stdout.write(
        json.dumps((result_type, data),
                   cls=cosmic_ray.json_util.JSONEncoder))

COMMAND_HANDLER_MAP = {
    'baseline':      handle_baseline,
    'counts':        handle_counts,
    'exec':          handle_exec,
    'help':          handle_help,
    'init':          handle_init,
    'load':          handle_load,
    'report':        handle_report,
    'run':           handle_run,
    'survival-rate': handle_survival_rate,
    'test-runners':  handle_test_runners,
    'operators':     handle_operators,
    'worker':        handle_worker,
}

OPTIONS = """cosmic-ray

Usage: cosmic-ray [options] <command> [<args> ...]

options:
  --help     Show this screen.
  --verbose  Produce more verbose output

Available commands:
  {}

See 'cosmic-ray help <command>' for help on specific commands.
""".format('\n  '.join(sorted(COMMAND_HANDLER_MAP)))


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    configuration = docopt.docopt(
        OPTIONS,
        argv=argv,
        options_first=True,
        version='cosmic-ray v.2')
    if configuration['--verbose']:
        logging.basicConfig(level=logging.INFO)
        argv.remove('--verbose')

    command = configuration['<command>']
    if command is None:
        command = 'help'

    try:
        handler = COMMAND_HANDLER_MAP[command]
    except KeyError:
        LOG.error('"%s" is not a valid cosmic-ray command', command)
        handler = handle_help
        argv = ['help']

    sub_config = docopt.docopt(
        handler.__doc__,
        argv,
        version='cosmic-ray v.2')

    sys.exit(handler(sub_config))

if __name__ == '__main__':
    main()
