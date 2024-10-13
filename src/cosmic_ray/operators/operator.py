"Implementation of operator base class."

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Optional


class Operator(ABC):
    """The mutation operator base class."""

    @abstractmethod
    def mutation_positions(self, node):
        """All positions where this operator can mutate ``node``.

        An operator might be able to mutate a node in multiple ways, and this
        function should produce a position description for each of these
        mutations. Critically, if an operator can make multiple mutations to the
        same position, this should produce a position for each of these
        mutations (i.e. multiple identical positions).

        Args:
            node: The AST node being mutated.

        Returns:
            An iterable of ``((start-line, start-col), (stop-line, stop-col))``
            tuples describing the locations where this operator will mutate ``node``.
        """

    @abstractmethod
    def mutate(self, node, index):
        """Mutate a node in an operator-specific manner.

        Return the new, mutated node. Return ``None`` if the node has
        been deleted. Return ``node`` if there is no mutation at all for
        some reason.
        """

    @classmethod
    def arguments(cls) -> Sequence["Argument"]:
        """Sequence of Arguments that the operator accepts.

        Returns: A Sequence of Argument instances
        """
        return ()

    @classmethod
    @abstractmethod
    def examples(cls):
        """Examples of the mutations that this operator can make.

        This is primarily for testing purposes, but it could also be used for
        documentation.

        Each example takes the following arguments:
            pre_mutation_code: code prior to applying the mutation.
            post_mutation_code: code after (successfully) applying the mutation.
            occurrence: the index of the occurrence to which the mutation is
                        applied (optional, default=0).
            operator_args: a dictionary of arguments to be **-unpacked to the
                           operator (optional, default={}).

        Returns: An iterable of Examples.
        """


@dataclasses.dataclass(frozen=True)
class Argument:
    name: str
    description: str


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
