"""Operator-provider plugin for all core cosmic ray operators.
"""

import itertools

from . import (binary_operator_replacement,
               boolean_replacer,
               break_continue,
               comparison_operator_replacement,
               exception_replacer,
               number_replacer,
               remove_decorator,
               unary_operator_replacement,
               zero_iteration_loop)


_OPERATORS = {
    op.__name__: op
    for op
    in itertools.chain(
        binary_operator_replacement.operators(),
        comparison_operator_replacement.operators(),
        unary_operator_replacement.operators(),
        (boolean_replacer.AddNot,
         boolean_replacer.ReplaceTrueFalse,
         boolean_replacer.ReplaceAndWithOr,
         boolean_replacer.ReplaceOrWithAnd,
         break_continue.ReplaceBreakWithContinue,
         break_continue.ReplaceContinueWithBreak,
         exception_replacer.ExceptionReplacer,
         number_replacer.NumberReplacer,
         remove_decorator.RemoveDecorator,
         zero_iteration_loop.ZeroIterationLoop))
}


class OperatorProvider:
    """Provider for all of the core Cosmic Ray operators."""

    def __iter__(self):
        return iter(_OPERATORS)

    def __getitem__(self, name):
        return _OPERATORS[name]
