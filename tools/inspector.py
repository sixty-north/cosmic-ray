# This is just a simple example of how to inspect ASTs visually.
#
# This can be useful for developing new operators, etc.

import ast

from cosmic_ray.mutating import MutatingCore
from cosmic_ray.operators.comparison_operator_replacement import MutateComparisonOperator

code = "((x is not y) ^ (x is y))"
node = ast.parse(code)
print()
print(ast.dump(node))

core = MutatingCore(0)
operator = MutateComparisonOperator(core)
new_node = operator.visit(node)
print()
print(ast.dump(new_node))
