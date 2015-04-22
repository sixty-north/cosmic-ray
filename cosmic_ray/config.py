"""cosmic-ray

Usage:
  cosmic-ray [options] [--exclude-modules=P ...] <module> <test-dir>

Options:
  -h --help           Show this screen.
  --timeout=T         Maximum time (seconds) a mutant may run [default: 5]
  --verbose           Produce verbose output
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --config=F          Name of config file to load [default: .cosmic-ray.yaml]
  --exclude-modules=P Pattern of module names to exclude from mutation
"""

import docopt


def load_configuration():
    cl_arguments = docopt.docopt(__doc__, version='cosmic-ray v.2')
    return cl_arguments

    # config_file = cl_arguments['--config']

    # if os.path.exists(config_file):
    #     LOG.info('Loading config file %s.', config_file)
    #     with open(config_file, 'rt', encoding='utf-8') as f:

    # else:
    #     LOG.info('Config file %s not found. Ignoring.', config_file)
