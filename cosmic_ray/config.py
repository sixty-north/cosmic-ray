"""cosmic-ray

Usage:
  cosmic-ray run [options] [--exclude-modules=P ...] <top-module> <test-dir>
  cosmic-ray load <config-file>

Options:
  -h --help           Show this screen.
  --timeout=T         Maximum time (seconds) a mutant may run [default: 5]
  --verbose           Produce verbose output
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation
"""

import docopt


def load_file(config_file):
    """Read configuration from a file.

    This reads `config_file`, yielding each non-empty line with
    whitespace and comments stripped off.
    """
    with open(config_file, 'rt', encoding='utf-8') as f:
        for line in f:
            line = line.split('#')[0] # Remove comments
            line = line.strip()       # Remove edge-whitespace
            if line:
                yield line


def load_configuration():
    config = docopt.docopt(__doc__, version='cosmic-ray v.2')

    if config['load']:
        filename = config['<config-file>']
        args = list(load_file(filename))
        config = docopt.docopt(__doc__, argv=args, version='cosmic-ray v.2')

    return config
