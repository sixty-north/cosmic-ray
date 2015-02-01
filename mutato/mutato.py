# Find all of the modules that need to be mutated
# Create ASTs for all of the modules
# Foreach AST:
#    foreach operation:
#        foreach location in AST where op applies:
#            apply op to location
#            Make that AST active/replace old module with new
#            run all tests
#            If not failures, mutant survived!

import ast

from .find_modules import find_modules


def mutato(module_name):
    asts = {path: ast.parse(path)
            for path in find_modules(module_name)}
