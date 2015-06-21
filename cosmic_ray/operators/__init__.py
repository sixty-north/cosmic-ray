import stevedore.extension

from .operator import Operator


def all_operators():
    # We don't use the extensions directly. This just forces importing
    # of modules which contain operators.
    stevedore.extension.ExtensionManager(
        namespace='cosmic_ray.operators')

    return Operator.__subclasses__()
