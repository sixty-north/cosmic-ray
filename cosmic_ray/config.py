"""cosmic-ray

Usage:
  cosmic-ray run [options] [--exclude-modules=P ...] (--timeout=T | --baseline=M) <top-module> <test-dir>
  cosmic-ray load <config-file>
  cosmic-ray test-runners

Options:
  -h --help           Show this screen.
  --timeout=T         Maximum time (seconds) a mutant may run
  --baseline=M        Calculate timeout as M times a baseline test run
  --verbose           Produce verbose output
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation
  --num-testers=N     Number of concurrent testers to run (0 = os.cpu_count()) [default: 0]
"""

import docopt
from transducer.functional import compose
from transducer.lazy import transduce
from transducer.transducers import filtering, mapping


# This is really an experiment in using transducers in "the real
# world". You could accomplish the same parsing goals in fewer lines
# (and probably more quickly) using more traditional means. But this
# approach does have a certain charm and elegance to it.
REMOVE_COMMENTS = mapping(lambda x: x.split('#')[0])
REMOVE_WHITESPACE = mapping(str.strip)
NON_EMPTY = filtering(bool)
PARSER = compose(REMOVE_COMMENTS,
                 REMOVE_WHITESPACE,
                 NON_EMPTY)


def load_file(config_file):
    """Read configuration from a file.

    This reads `config_file`, yielding each non-empty line with
    whitespace and comments stripped off.
    """
    with open(config_file, 'rt', encoding='utf-8') as f:
        yield from transduce(PARSER, f)


def load_configuration():
    config = docopt.docopt(__doc__, version='cosmic-ray v.2')

    if config['load']:
        filename = config['<config-file>']
        args = load_file(filename)
        config = docopt.docopt(__doc__, argv=args, version='cosmic-ray v.2')

    return config
