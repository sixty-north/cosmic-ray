"""Operator-provider plugin for all core cosmic ray operators.
"""

import itertools

from . import (binary_operator_replacement, boolean_replacer, break_continue,
               comparison_operator_replacement, exception_replacer,
               no_op, number_replacer, remove_decorator, unary_operator_replacement,
               zero_iteration_for_loop)

# NB: The no_op operator gets special handling. We don't include it in iteration of the
# available operators. However, you can request it from the provider by name. This lets us
# use it in a special way: to request that a worker perform a no-op test run while preventing
# it from being used in normal mutations testing runs.

_OPERATORS = {
    op.__name__: op
    for op in itertools.chain(binary_operator_replacement.operators(
    ), comparison_operator_replacement.operators(
    ), unary_operator_replacement.operators(), (
        boolean_replacer.AddNot, boolean_replacer.ReplaceTrueWithFalse,
        boolean_replacer.ReplaceFalseWithTrue,
        boolean_replacer.ReplaceAndWithOr, boolean_replacer.ReplaceOrWithAnd,
        break_continue.ReplaceBreakWithContinue,
        break_continue.ReplaceContinueWithBreak,
        exception_replacer.ExceptionReplacer,
        number_replacer.NumberReplacer,
        remove_decorator.RemoveDecorator,
        zero_iteration_for_loop.ZeroIterationForLoop))
}


class OperatorProvider:
    """Provider for all of the core Cosmic Ray operators."""

    def __iter__(self):
        return iter(_OPERATORS)

    def __getitem__(self, name):
        if name == 'NoOp':
            return no_op.NoOp

        return _OPERATORS[name]
