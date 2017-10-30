from stevedore import driver, ExtensionManager


def get_operator(name):
    """Get an operator class from a plugin.

    Attrs:
        name: The name of the plugin containing the operator class.

    Returns: The operator *class object* (i.e. not an instance) provided by the
        plugin named `name`.
    """
    return ExtensionManager('cosmic_ray.operators')[name].plugin


def operator_names():
    """Get an iterable of all operator plugin names."""
    return ExtensionManager('cosmic_ray.operators').names()


def get_test_runner(name, test_args):
    """Get a test-runner instance by name."""
    test_runner_manager = driver.DriverManager(
        namespace='cosmic_ray.test_runners',
        name=name,
        invoke_on_load=True,
        invoke_args=(test_args,),
    )

    return test_runner_manager.driver


def test_runner_names():
    """Get iterable of test-runner plugin names."""
    return ExtensionManager('cosmic_ray.test_runners').names()


def get_execution_engine(name):
    manager = driver.DriverManager(
        namespace='cosmic_ray.execution_engines',
        name=name,
        invoke_on_load=True)

    return manager.driver


def execution_engine_names():
    """Get iterable of execution-enginer plugin names."""
    return ExtensionManager('cosmic_ray.execution_engines').names()
