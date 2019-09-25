"""Query and retrieve the various plugins in Cosmic Ray.
"""

import logging
import re

from stevedore import driver, ExtensionManager

log = logging.getLogger()


def _log_extension_loading_failure(_mgr, ep, err):
    # We have to log at the `error` level here as opposed to, say, `info`
    # because logging isn't configure when we reach here. We need this infor to
    # print with the default logging settings.
    log.error('Operator provider load failure: extension-point="%s", err="%s"',
              ep, err)


OPERATOR_PROVIDERS = None


def load_operators(exclude_operators):
    global OPERATOR_PROVIDERS
    re_exclude_operators = [re.compile(e) for e in exclude_operators]

    operator_providers = ExtensionManager('cosmic_ray.operator_providers',
                                          on_load_failure_callback=_log_extension_loading_failure)

    OPERATOR_PROVIDERS = {}
    for e in operator_providers:
        provider_plugin = e.plugin()

        for op_name in provider_plugin:
            full_op_name = '%s/%s' % ((e.name), op_name)

            # Filter out operators according to exclude_operators
            if not any(r.match(full_op_name) for r in re_exclude_operators):
                    OPERATOR_PROVIDERS[full_op_name] = provider_plugin[op_name]


def get_operator(name):
    """Get an operator class from a provider plugin.

    Attrs:
        name: The name of the operator class.

    Returns: The operator *class object* (i.e. not an instance).
    """
    return OPERATOR_PROVIDERS[name]


def operator_names():
    """Get all operator names.

    Returns: A sequence of operator names.
    """
    return OPERATOR_PROVIDERS.keys()


def get_interceptor(name):
    """Get an interceptor by name.

    Attrs:
        name: The name of the plugin containing the interceptor.

    Returns: A callable object which must accept a single `WorkDB` argument.
    """
    return ExtensionManager(
        'cosmic_ray.interceptors',
        on_load_failure_callback=_log_extension_loading_failure,
    )[name].plugin


def interceptor_names():
    """Get all interceptor plugin names.

    Returns: A sequence of interceptor plugin names.
    """
    return ExtensionManager(
        'cosmic_ray.interceptors',
        on_load_failure_callback=_log_extension_loading_failure,
    ).names()


def get_execution_engine(name):
    """Get the execution engine by name."""
    manager = driver.DriverManager(
        namespace='cosmic_ray.execution_engines',
        name=name,
        invoke_on_load=True,
        on_load_failure_callback=_log_extension_loading_failure,
    )

    return manager.driver


def execution_engine_names():
    """Get all execution-engine plugin names.

    Returns: A sequence of execution-engine names.
    """
    return ExtensionManager(
        'cosmic_ray.execution_engines',
        on_load_failure_callback=_log_extension_loading_failure,
    ).names()
