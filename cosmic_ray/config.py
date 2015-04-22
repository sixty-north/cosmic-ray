"""cosmic-ray

Usage:
  cosmic-ray [options] [--exclude-modules=P ...]

Options:
  -h --help           Show this screen.
  --timeout=T         Maximum time (seconds) a mutant may run [default: 5]
  --verbose           Produce verbose output
  --no-local-import   Allow importing module from the current directory
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --config=F          Name of config file to load [default: .cosmic-ray.conf]
  --exclude-modules=P Pattern of module names to exclude from mutation
  -m M                Module/package to mutate
  -t T                Directory containing tests to run
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
