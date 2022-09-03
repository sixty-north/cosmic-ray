"""Data class to store example applications of mutation operators.
   These structures are used for testing purposes."""
import dataclasses

from typing import Optional


@dataclasses.dataclass(frozen=True)
class Example:
    """A structure to store pre and post mutation operator code snippets,
       including optional specification of occurrence and operator args.

       This is used for testing whether the pre-mutation code is correctly
       mutated to the post-mutation code at the given occurrence (if specified)
       and for the given operator args (if specified).
    """

    pre_mutation_code: str
    post_mutation_code: str
    occurrence: Optional[int] = 0
    operator_args: Optional[dict] = None

    def __post_init__(self):
        if not self.operator_args:
            object.__setattr__(self, "operator_args", {})
