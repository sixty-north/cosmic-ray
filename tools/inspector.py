# This is just a simple example of how to inspect ASTs visually.
#
# This can be useful for developing new operators, etc.

import ast

from cosmic_ray.operators.relational_operator_replacement import ReplaceEq


node = ast.parse('if x == 1: pass')
print(ast.dump(node))

node = ReplaceEq(0).visit(node)
print(ast.dump(node))
