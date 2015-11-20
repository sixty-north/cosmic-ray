"""This is the command-line program for cosmic ray.

Here we manage command-line parsing and launching of the internal
machinery that does mutation testing.
"""

import logging
import sys

import docopt
from transducer.functional import compose
from transducer.lazy import transduce
from transducer.transducers import filtering, mapping

from cosmic_ray import config, mutating, plugins
import cosmic_ray.operators
from cosmic_ray.find_modules import find_modules
import cosmic_ray.processing
from cosmic_ray.testing.test_runner import Outcome
from cosmic_ray.worker import worker


LOG = logging.getLogger()

OPTIONS = """cosmic-ray

Usage: cosmic-ray [--verbose] [--help] <command> [<args> ...]

options:
  --help     Show this screen.
  --verbose  Produce more verbose output

Available commands:
  run
  load
  test-runners
  worker

See 'cosmic-ray help <command>' for help on specific commands.
"""

# This is really an experiment in using transducers in "the real
# world". You could accomplish the same parsing goals in fewer lines
# (and probably more quickly) using more traditional means. But this
# approach does have a certain charm and elegance to it.
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
        yield from transduce(CONFIG_FILE_PARSER, f)


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


def handle_run(configuration):
    """usage: cosmic-ray run [options] [--exclude-modules=P ...] (--timeout=T | --baseline=M) <top-module> <test-dir>

options:
  --verbose           Produce verbose output
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation
  --num-testers=N     Number of concurrent testers to run (0 = os.cpu_count()) [default: 0]
"""
    test_runner = plugins.get_test_runner(
        configuration['--test-runner'],
        configuration['<test-dir>'])

    if configuration['--timeout'] is not None:
        timeout = float(configuration['--timeout'])
    else:
        baseline_mult = float(configuration['--baseline'])
        assert baseline_mult is not None
        timeout = config.find_baseline(test_runner) * baseline_mult
    LOG.info('timeout = {} seconds'.format(timeout))

    num_testers = config.get_num_testers(int(configuration['--num-testers']))

    if not configuration['--no-local-import']:
        sys.path.insert(0, '')

    modules = config.filtered_modules(
        find_modules(configuration['<top-module>']),
        configuration['--exclude-modules'])

    operators = cosmic_ray.operators.all_operators()

    mutation_records = mutating.create_mutants(modules, operators)

    summarizer = Summarizer()

    cosmic_ray.processing.test_mutants(
        mutation_records,
        test_runner,
        num_testers,
        timeout,
        summarizer)

    total_count = sum(summarizer.outcomes.values())

    if total_count > 0:
        print('Survival rate: {:0.2f}%'.format(
            100 * summarizer.outcomes[Outcome.SURVIVED] / total_count))
    else:
        print('No tests run (no mutations generated).')  # pylint:disable=superfluous-parens


def handle_test_runners(config):
    """usage: cosmic-ray test-runners

List the available test-runner plugins.
"""
    print('\n'.join(plugins.test_runners()))
    return 0


def handle_operators(config):
    """usage: cosmic-ray operators

List the available operator plugins.
"""
    print('\n'.join(plugins.operators()))
    return 0


def handle_worker(config):
    """usage: cosmic-ray worker [options] <module> <operator> <occurrence> <test-runner> <test-dir> <timeout>

options:
  --verbose           Produce verbose output
  --no-local-import   Disallow importing module from the current directory
"""
    if not config['--no-local-import']:
        sys.path.insert(0, '')

    operator = plugins.get_operator(config['<operator>'])
    test_runner = plugins.get_test_runner(
        config['<test-runner>'],
        config['<test-dir>'])

    result = worker(
        config['<module>'],
        operator,
        int(config['<occurrence>']),
        test_runner,
        float(config['<timeout>']))
    print(result)


COMMAND_HANDLER_MAP = {
    'help':         handle_help,
    'load':         handle_load,
    'run':          handle_run,
    'test-runners': handle_test_runners,
    'operators':    handle_operators,
    'worker':       handle_worker,
}


class Summarizer:
    """A result-handler that collects simple statistics.
    """
    def __init__(self):
        self.outcomes = {o: 0 for o in Outcome}

    def handle_result(self, mutation_record, test_result):
        self.outcomes[test_result.outcome] += 1


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
