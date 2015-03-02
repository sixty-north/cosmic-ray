import ast
import copy
import itertools
import logging

log = logging.getLogger()


class Operator(ast.NodeTransformer):
    """A base class for mutation operators.

    This takes care of the basic book-keeping that all operators need
    to do.
    """
    def __init__(self, target):
        self._target = target
        self._count = 0
        self._activated = False

    @property
    def activated(self):
        return self._activated

    def visit_mutation_site(self, node):
        """Potentially mutate `node`, returning the mutated version.

        Subclasses should call this when their AST iteration reaches a
        potential mutation site. If that site is schedule for
        mutation, the subclass instance will be asked to perform the
        mutation.
        """
        if self._count == self._target:
            self._activated = True
            if hasattr(node, 'lineno'):
                log.info('{}: mutating line number {}'.format(
                    self.__class__, node.lineno))
            node = self.mutate(node)

        self._count += 1
        return node

    def mutate(self, node):
        """Mutate a node in an operator-specific manner.

        Return the new, mutated node. Return `None` if the node has
        been deleted. Return `node` if there is no mutation at all for
        some reason.
        """
        raise NotImplementedError(
            'Mutation operators must implement "mutate()".')

    @classmethod
    def bombard(cls, node):
        """Bombard `node` with cosmic rays, generating a sequence of odious
        mutants.

        The returns an iterable sequence of mutated copies of `node`,
        with one mutant for each potential mutation site in `node`
        with respect to the `Operator` subclass which is performing
        the mutations.
        """
        for target in itertools.count():
            operator = cls(target)
            clone = operator.visit(copy.deepcopy(node))
            if not operator.activated:
                break

            yield clone
