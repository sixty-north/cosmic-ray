"Implementation of operator base class."

from abc import ABC, abstractmethod


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
