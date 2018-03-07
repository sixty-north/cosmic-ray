"Implementation of operator base class."

from abc import ABCMeta, abstractmethod
import ast


class Operator(ast.NodeTransformer):
    """
    A base class for all mutation operators.

    This takes care of the basic book-keeping that all operators need
    to do. All operators *must* derive from this class since that's
    how we keep track of them.
    """

    def __init__(self, core):
        self._core = core

    @property
    def core(self):
        """The core behavior of the operator."""
        return self._core

    def repr_args(self):
        "Extra arguments to display in operator reprs."
        return self.core.repr_args()

    def visit_mutation_site(self, node, num_mutations=1):
        """Subclasses call this when they encounter a node they can
         potentially mutate.

        This functions delegates to the core, letting it do whatever it needs
        to do.
        """
        return self.core.visit_mutation_site(node, self, num_mutations)

    def mutate(self, node, idx):
        """Mutate a node in an operator-specific manner.

        Return the new, mutated node. Return `None` if the node has
        been deleted. Return `node` if there is no mutation at all for
        some reason.
        """
        raise NotImplementedError(
            'Mutation operators must implement "mutate()".')

    def __repr__(self):
        repr_args = [('core', self.core.__class__.__name__)]
        repr_args.extend(self.core.repr_args())
        args = ['{}={}'.format(k, v)
                for k, v
                in repr_args]

        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(args))


def _op_name(from_op, to_op):
    assert from_op or to_op, 'Cannot make replacement operator from None to None'

    if from_op is None:
        return 'Insert_{}'.format(to_op.__name__)
    elif to_op is None:
        return 'Delete_{}'.format(from_op.__name__)

    return '{}_{}'.format(from_op.__name__, to_op.__name__)


class ReplacementOperatorMeta(type):
    """Metaclass for mutation operators that replace Python operators.

    This does a few things:

    - Sets the name of the class object based on the class declaration *and* the from-/to-operators.
    - Makes the from-/to-operators available as class members.
    - Adds `Operator` as a base class.
    """
    def __init__(cls, name, bases, namespace, from_op, to_op, **kwargs):
        super().__init__(name, bases, namespace, **kwargs)

    def __new__(cls, name, bases, namespace, from_op, to_op, **kwargs):
        name = '{}_{}'.format(
            name,
            _op_name(from_op, to_op))
        bases = bases + (Operator,)
        namespace['from_op'] = from_op
        namespace['to_op'] = to_op
        return super().__new__(cls, name, bases, namespace, **kwargs)
