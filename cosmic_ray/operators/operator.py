import ast
import copy
import itertools

from ..util import get_line_number


def _full_module_name(obj):
    return '{}.{}'.format(
        obj.__class__.__module__,
        obj.__class__.__name__)


class Operator(ast.NodeTransformer):
    """A base class for all mutation operators.

    This takes care of the basic book-keeping that all operators need
    to do. All operators *must* derive from this class since that's
    how we keep track of them.
    """
    def __init__(self, target):
        self._target = target
        self._count = 0
        self._activation_record = None

    @property
    def activation_record(self):
        """The activation record for the operator.

        The activation record is a dict describing where and how the
        operator was applied.
        """
        return self._activation_record

    def visit_mutation_site(self, node):
        """Potentially mutate `node`, returning the mutated version.

        Subclasses should call this when their AST iteration reaches a
        potential mutation site. If that site is scheduled for
        mutation, the subclass instance will be asked to perform the
        mutation.
        """
        if self._count == self._target:
            self._activation_record = {
                'operator': _full_module_name(self),
                'description': str(self),
                'line_number': get_line_number(node)
            }

            old_node = node
            node = self.mutate(old_node)
            ast.copy_location(node, old_node)

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
            mutant = operator.visit(copy.deepcopy(node))
            if not operator.activation_record:
                break

            yield operator.activation_record, mutant
