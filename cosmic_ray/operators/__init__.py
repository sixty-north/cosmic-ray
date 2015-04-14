from .operator import Operator


def all_operators():
    return Operator.__subclasses__()
