from stevedore import driver, ExtensionManager


def test_runner(name, test_dir):
    """Get a test-runner instance by name.
    """
    test_runner_manager = driver.DriverManager(
        namespace='cosmic_ray.test_runners',
        name=name,
        invoke_on_load=True,
        invoke_args=(test_dir,),
    )

    return test_runner_manager.driver


def test_runners():
    """Get iterable of test-runner plugin names.
    """
    return ExtensionManager('cosmic_ray.test_runners').names()
