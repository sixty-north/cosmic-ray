"""This is the command-line program for cosmic ray.

Here we manage command-line parsing and launching of the internal
machinery that does mutation testing.
"""
import itertools
import json
import logging
import pprint
import sys

import docopt
import transducer.eager
from transducer.functional import compose
import transducer.lazy
from transducer.transducers import filtering, mapping

import cosmic_ray.counting
import cosmic_ray.modules
import cosmic_ray.json_util
import cosmic_ray.worker
import cosmic_ray.testing
import cosmic_ray.timing
from cosmic_ray.work_db import use_db, WorkDB


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
        LOG.error('"{}" is not a valid cosmic-ray command'.format(command))
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
    """usage: cosmic-ray baseline [options] <top-module> <test-dir>

Run an un-mutated baseline of <top-module> using the tests in <test-dir>.
This is largely like running a "worker" process, with the difference
that a baseline run doesn't mutate the code.

options:
  --verbose           Produce verbose output
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
"""
    sys.path.insert(0, '')
    test_runner = cosmic_ray.plugins.get_test_runner(
            configuration['--test-runner'],
            configuration['<test-dir>'])

    test_runner()


def _get_db_name(session_name):
    return '{}.json'.format(session_name)


def handle_init(configuration):
    """usage: cosmic-ray init [options] [--exclude-modules=P ...] (--timeout=T | --baseline=M) <session-name> <top-module> <test-dir>

Initialize a mutation testing run. The primarily creates a database of "work to
be done" which describes all of the mutations and test runs that need to be
executed for a full mutation testing run. The testing run will mutate
<top-module> (and submodules) using the tests in <test-dir>. This doesn't
actually run any tests. Instead, it scans the modules-under-test and simply
generates the work order which can be executed with other commands.

The session-name argument identifies the run you're creating. It's most
important role is that it's used to name the database file.

options:
  --verbose           Produce verbose output
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
        timeout = baseline_mult * cosmic_ray.timing.run_baseline(
            configuration['--test-runner'],
            configuration['<top-module>'],
            configuration['<test-dir>'])

    LOG.info('timeout = {} seconds'.format(timeout))

    modules = cosmic_ray.modules.filtered_modules(
        cosmic_ray.modules.find_modules(configuration['<top-module>']),
        configuration['--exclude-modules'])

    operators = cosmic_ray.plugins.operator_names()

    counts = cosmic_ray.counting.count_mutants(modules, operators)

    db_name = _get_db_name(configuration['<session-name>'])

    with use_db(db_name) as db:
        db.set_work_parameters(
            test_runner=configuration['--test-runner'],
            test_directory=configuration['<test-dir>'],
            timeout=timeout)

        db.clear_work_items()

        db.add_work_items(
            (module.__name__, opname, occurrence)
            for module, ops in counts.items()
            for opname, count in ops.items()
            for occurrence in range(count))


def handle_exec(configuration):
    """usage: cosmic-ray exec [options] <session-name>

Perform the remaining work to be done in the specified session. This requires
that the rest of your mutation testing infrastructure (e.g. worker processes)
are already running.

options:
  --verbose           Produce verbose output

    """
    db_name = _get_db_name(configuration['<session-name>'])

    with use_db(db_name, mode=WorkDB.Mode.open) as db:
        test_runner, test_directory, timeout = db.get_work_parameters()
        results = cosmic_ray.worker.execute_jobs(test_runner,
                                                 test_directory,
                                                 timeout,
                                                 db.pending_work)

        for r in results:
            job_id, (result_type, result_data) = r.get()
            db.add_results(job_id, result_type, result_data)


def handle_run(configuration):
    """usage: cosmic-ray run [options] [--exclude-modules=P ...] (--timeout=T | --baseline=M) <session-name> <top-module> <test-dir>

This simply runs the "init" command followed by the "exec" command.

It's important to remember that "init" clears the session database, including
any results you may have already received. So DO NOT USE THIS COMMAND TO
CONTINUE EXECUTION OF AN INTERRUPTED SESSION! If you do this, you will lose any
existing results.

options:
  --verbose           Produce verbose output
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation

    """
    handle_init(configuration)
    handle_exec(configuration)


def handle_report(configuration):
    """usage: cosmic-ray report <session-name>

Print a nicely formatted report of test results and some basic statistics.

    """
    def print_item(item):
        print('job ID:', item.eid)
        print('module:', item['module-name'])
        print('operator:', item['op-name'])
        print('occurrence:', item['occurrence'])
        try:
            print('result type:', item['results-type'])
            print('data:', item['results-data'])
        except KeyError:
            pass

    def get_kills(db):
        completed = filtering(lambda r: 'results-type' in r)
        normal = filtering(lambda r: r['results-type'] == 'normal')
        killed = filtering(lambda r: r['results-data'][1][0] == 'Outcome.KILLED')
        find_kills = compose(completed, normal, killed)
        return transducer.eager.transduce(find_kills, transducer.reducers.Appending(), db.work_items)

    db_name = _get_db_name(configuration['<session-name>'])

    with use_db(db_name) as db:
        for item in db.work_items:
            print_item(item)
            print('')

        total_jobs =  sum(1 for _ in db.work_items)
        pending_jobs = sum(1 for _ in db.pending_work)
        completed_jobs = total_jobs - pending_jobs
        kills = get_kills(db)
        print('total jobs:', total_jobs)

        if completed_jobs > 0:
            print('complete: {}%'.format(completed_jobs / total_jobs * 100))
            print('survival rate: {}%'.format((1 - len(kills) / completed_jobs) * 100))
        else:
            print('no jobs completed')


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

    modules = cosmic_ray.modules.filtered_modules(
        cosmic_ray.modules.find_modules(configuration['<top-module>']),
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
    """usage: cosmic-ray worker [options] <module> <operator> <occurrence> <test-runner> <test-dir> <timeout>

Run a worker process which performs a single mutation and test run. Each
worker does a minimal, isolated chunk of work: it mutates the <occurence>-th
instance of <operator> in <module>, runs the test suite defined by
<test-runner> and <test-dir>, prints the results, and exits. If the test run
takes longer than <timeout>, the test it killed.

Normally you won't run this directly. Rather, it will be launched by celery
worker tasks.

options:
  --verbose           Produce verbose output
  --no-local-import   Disallow importing module from the current directory
"""
    if not config['--no-local-import']:
        sys.path.insert(0, '')

    operator = cosmic_ray.plugins.get_operator(config['<operator>'])
    test_runner = cosmic_ray.plugins.get_test_runner(
        config['<test-runner>'],
        config['<test-dir>'])

    result_type, data = cosmic_ray.worker.worker(
        config['<module>'],
        operator,
        int(config['<occurrence>']),
        test_runner,
        float(config['<timeout>']))

    if result_type == 'exception':
        data = str(data)

    sys.stdout.write(
        json.dumps((result_type, data),
                   cls=cosmic_ray.json_util.JSONEncoder))

COMMAND_HANDLER_MAP = {
    'baseline':     handle_baseline,
    'counts':       handle_counts,
    'exec':         handle_exec,
    'help':         handle_help,
    'init':         handle_init,
    'load':         handle_load,
    'report':       handle_report,
    'run':          handle_run,
    'test-runners': handle_test_runners,
    'operators':    handle_operators,
    'worker':       handle_worker,
}

OPTIONS = """cosmic-ray

Usage: cosmic-ray [--verbose] [--help] <command> [<args> ...]

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

    command = configuration['<command>']
    if command is None:
        command == 'help'

    try:
        handler = COMMAND_HANDLER_MAP[command]
    except KeyError:
        LOG.error('"{}" is not a valid cosmic-ray command'.format(command))
        handler = handle_help
        argv = ['help']

    sub_config = docopt.docopt(
        handler.__doc__,
        argv,
        version='cosmic-ray v.2')

    sys.exit(handler(sub_config))

if __name__ == '__main__':
    main()
