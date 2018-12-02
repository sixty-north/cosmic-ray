"""Implementation of the replace-break-with-continue and
replace-continue-with-break operators.
"""

from .keyword_replacer import KeywordReplacementOperator


class ReplaceBreakWithContinue(KeywordReplacementOperator):
    "Operator which replaces 'break' with 'continue'."
    from_keyword = 'break'
    to_keyword = 'continue'


class ReplaceContinueWithBreak(KeywordReplacementOperator):
    "Operator which replaces 'continue' with 'break'."
    from_keyword = 'continue'
    to_keyword = 'break'
