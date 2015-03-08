# These are imported purely to "register" them.
import cosmic_ray.operators.arithmetic_operator_deletion
import cosmic_ray.operators.number_replacer
import cosmic_ray.operators.relational_operator_replacement

from .operator import Operator

def all_operators():
    return Operator.__subclasses__()
