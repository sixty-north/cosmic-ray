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
