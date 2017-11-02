# Generate a new configuration string.

import qprompt

import cosmic_ray.plugins

TEMPLATE = '''module: {module}

baseline: 10

exclude-modules:

test-runner:
  name: {test_runner}
  args: {test_args}

execution-engine:
  name: {engine}
'''


def new_config():
    """Prompt user for config variables and generate new config.

    Returns: A new configuration as a single string.
    """
    conf = {'module': qprompt.ask_str("Top-level module")}

    menu = qprompt.Menu()
    test_runners = cosmic_ray.plugins.test_runner_names()
    for at_pos, test_runner in enumerate(test_runners):
        menu.add(str(at_pos), test_runner)
    conf['test_runner'] = menu.show(header="Test runner",
                                    returns="desc")

    conf['test_args'] = qprompt.ask_str('Test args')

    menu = qprompt.Menu()
    for at_pos, engine_name in enumerate(cosmic_ray.plugins.execution_engine_names()):
        menu.add(str(at_pos), engine_name)
    conf['engine'] = menu.show(header="Execution engine",
                               returns="desc")
    return TEMPLATE.format(**conf)
