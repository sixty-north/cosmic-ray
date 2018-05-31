import logging
import sys

import cosmic_ray.config
import cosmic_ray.counting
import cosmic_ray.find_modules
import cosmic_ray.plugins
import cosmic_ray.timing
import cosmic_ray.worker
import docopt

LOG = logging.getLogger()

OPTIONS = """usage: frontend.py [options] [--exclude-modules=P ...] (--timeout=T | --baseline=M) <top-module> <test-dir>

options:
  --verbose           Produce verbose output
  --test-runner=R     Test-runner plugin to use [default: unittest]
  --exclude-modules=P Pattern of module names to exclude from mutation
"""


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    configuration = docopt.docopt(
        OPTIONS,
        argv=argv,
        options_first=True,
        version='cosmic-ray v.3')

    if configuration['--verbose']:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(name)s %(levelname)s %(message)s')

    # This lets us import modules from the current directory. Should probably
    # be optional, and needs to also be applied to workers!
    sys.path.insert(0, '')

    if configuration['--timeout'] is not None:
        timeout = float(configuration['--timeout'])
    else:
        test_runner = cosmic_ray.plugins.get_test_runner(
            configuration['--test-runner'],
            configuration['<test-dir>'])
        baseline_mult = float(configuration['--baseline'])
        assert baseline_mult is not None
        timeout = cosmic_ray.timing.time_execution(test_runner) * baseline_mult

    LOG.info('timeout = {} seconds'.format(timeout))

    modules = cosmic_ray.config.filtered_modules(
        cosmic_ray.find_modules.find_modules(configuration['<top-module>']),
        configuration['--exclude-modules'])

    operators = cosmic_ray.plugins.operator_names()

    counts = cosmic_ray.counting.count_mutants(modules, operators)

    results = (
        cosmic_ray.worker.worker_task.delay(module.__name__,
                                            opname,
                                            occurrence,
                                            configuration['--test-runner'],
                                            configuration['<test-dir>'],
                                            timeout)
        for module, ops in counts.items()
        for opname, count in ops.items()
        for occurrence in range(count))

    for r in results:
        print(r.get())

if __name__ == '__main__':
    main()
