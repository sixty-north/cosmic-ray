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
import transducer.functional
import transducer.lazy
import transducer.transducers

import cosmic_ray.counting
import cosmic_ray.modules
import cosmic_ray.json_util
import cosmic_ray.worker
import cosmic_ray.testing
import cosmic_ray.timing


LOG = logging.getLogger()

OPTIONS = """cosmic-ray

Usage: cosmic-ray [--verbose] [--help] <command> [<args> ...]

options:
  --help     Show this screen.
  --verbose  Produce more verbose output

Available commands:
  load
  operators
  run
  test-runners
  worker

See 'cosmic-ray help <command>' for help on specific commands.
"""

# This is really an experiment in using transducers in "the real
# world". You could accomplish the same parsing goals in fewer lines
# (and probably more quckly) using more traditional means. But this
# approach does have a certain charm and elegance to it.
REMOVE_COMMENTS = transducer.transducers.mapping(lambda x: x.split('#')[0])
REMOVE_WHITESPACE = transducer.transducers.mapping(str.strip)
NON_EMPTY = transducer.transducers.filtering(bool)
CONFIG_FILE_PARSER = transducer.functional.compose(REMOVE_COMMENTS,
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

Get help on a specific command.
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

Load a command configuration from a file and run it.
    """
    filename = config['<config-file>']
    argv = _load_file(filename)
    return main(argv=list(argv))


def handle_baseline(configuration):
    """usage: cosmic-ray baseline [options] <top-module> <test-dir>

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
    

def handle_run(configuration):
    """usage: cosmic-ray run [options] [--exclude-modules=P ...] (--timeout=T | --baseline=M) <top-module> <test-dir>

options:
  --verbose           Produce verbose output
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation
  --num-testers=N     Number of concurrent testers to run (0 = os.cpu_count()) [default: 0]
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

    results = [
        cosmic_ray.worker.worker_task.delay(module.__name__,
                                            opname,
                                            occurrence,
                                            configuration['--test-runner'],
                                            configuration['<test-dir>'],
                                            timeout)
        for module, ops in counts.items()
        for opname, count in ops.items()
        for occurrence in range(count)]

    for r in results:
        print(r.get())


def handle_counts(configuration):
    """usage: cosmic-ray counts [options] [--exclude-modules=P ...] <top-module>

options:
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation
  --num-testers=N     Number of concurrent testers to run (0 = os.cpu_count()) [default: 0]
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

options:
  --verbose           Produce verbose output
  --no-local-import   Disallow importing module from the current directory
"""
    if not config['--no-local-import']:
        sys.path.insert(0, '')

    operator = cosmic_ray.plugins.get_operator(config['<operator>'])
    cosmic_ray.testing.test_runner = cosmic_ray.plugins.get_test_runner(
        config['<test-runner>'],
        config['<test-dir>'])

    result = cosmic_ray.worker.worker(
        config['<module>'],
        operator,
        int(config['<occurrence>']),
        cosmic_ray.testing.test_runner,
        float(config['<timeout>']))
    sys.stdout.write(
        json.dumps(result,
                   cls=cosmic_ray.json_util.JSONEncoder))


COMMAND_HANDLER_MAP = {
    'baseline':     handle_baseline,
    'counts':       handle_counts,
    'help':         handle_help,
    'load':         handle_load,
    'run':          handle_run,
    'test-runners': handle_test_runners,
    'operators':    handle_operators,
    'worker':       handle_worker,
}


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
