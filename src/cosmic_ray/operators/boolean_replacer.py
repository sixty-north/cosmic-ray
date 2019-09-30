"Implementation of the boolean replacement operators."

import parso.python.tree
from parso.python.tree import Keyword, PythonNode, Operator as tree_Operator, \
    Function

from cosmic_ray.operators.util import ObjTest
from .keyword_replacer import KeywordReplacementOperator
from .operator import Operator


class ReplaceTrueWithFalse(KeywordReplacementOperator):
    """An that replaces True with False."""
    from_keyword = 'True'
    to_keyword = 'False'


class ReplaceFalseWithTrue(KeywordReplacementOperator):
    """An that replaces False with True."""
    from_keyword = 'False'
    to_keyword = 'To'


class KeywordNoAnnotationReplacementOperator(KeywordReplacementOperator):
    """
    Filter all keyword inside annotation:
    Example 'or' inside following sentence must be skipped for mutation
    >>> a: int or float = None
    >>> def f(a: int or float): pass
    >>> def g(a) -> int or float: pass
    """
    def mutation_positions(self, node):
        if ObjTest(node).match(Keyword):
            if self._is_def_function_annotation(node) or \
                    self._is_var_annotation(node) or \
                    self._is_def_function_var_annotation(node):
                return
        yield from super().mutation_positions(node)

    @staticmethod
    def _is_var_annotation(node: Keyword):
        """
        a: int or float = None

        ExprStmt(expr_stmt, [
            Name(name, 'a'),
            PythonNode(annassign, [          <-- test this
                Operator(operator, ':'),
                PythonNode(or_test, [
                    Name(name, 'int'),
                    Keyword(keyword, 'or'),  <-- node
                    Name(name, 'float'),
                ]),
                Operator(operator, '='),
                Keyword(keyword, 'None'),
            ]),
        ]),
        """
        t = ObjTest(node).parent
        while t:
            if t.match(PythonNode, type='annassign'):
                return True
            t = t.parent
        return False

    @staticmethod
    def _is_def_function_var_annotation(node: Keyword):
        """
        def f(a: int or float): pass

        Function(funcdef, [                          <-- recursion guard
            Keyword(keyword, 'def'),
            Name(name, 'f'),
            PythonNode(parameters, [
                Operator(operator, '('),
                Param(param, [
                    PythonNode(tfpdef, [             <-- test this
                        Name(name, 'a'),
                        Operator(operator, ':'),
                        PythonNode(or_test, [
                            Name(name, 'int'),
                            Keyword(keyword, 'or'),  <-- node
                            Name(name, 'float'),
                        ]),
                    ]),
                ]),
                Operator(operator, ')'),
            ]),
            Operator(operator, ':'),
            ...,
        ]),
        """
        t = ObjTest(node).parent
        while t and not t.match(Function, type='funcdef'):
            if t.match(PythonNode, type='tfpdef'):
                return True
            t = t.parent
        return False

    @staticmethod
    def _is_def_function_annotation(node: Keyword):
        """
        def f(a) -> int or float: pass

        Function(funcdef, [              <-- recursion guard
            Keyword(keyword, 'def'),
            Name(name, 'f'),
            PythonNode(parameters, [
                Operator(operator, '('),
                ...,
                Operator(operator, ')'),
            ]),
            Operator(operator, '->'),    <-- test this
            PythonNode(or_test, [
                Name(name, 'int'),
                Keyword(keyword, 'or'),  <-- node
                Name(name, 'float'),
            ]),
            Operator(operator, ':'),
            ...,
        ]),
        """
        t = ObjTest(node).parent
        while t and not t.match(Function, type='funcdef'):
            if t.match(PythonNode).get_previous_sibling(). \
                    match(tree_Operator, value='->'):
                return True
            t = t.parent
        return False


class ReplaceAndWithOr(KeywordNoAnnotationReplacementOperator):
    """An operator that swaps 'and' with 'or'."""
    from_keyword = 'and'
    to_keyword = 'or'

    @classmethod
    def examples(cls):
        return (
            ('x and y', 'x or y'),
        )


class ReplaceOrWithAnd(KeywordNoAnnotationReplacementOperator):
    """An operator that swaps 'or' with 'and'."""
    from_keyword = 'or'
    to_keyword = 'and'

    @classmethod
    def examples(cls):
        return (
            ('x or y', 'x and y'),
            ('a: int or float = None', 'a: int or float = None'),
            ('def f(a: int or float): pass', 'def f(a: int or float): pass'),
            ('def f() -> int or float: pass', 'def f() -> int or float: pass'),
        )


class AddNot(Operator):
    """
        An operator that adds the 'not' keyword to boolean expressions.

        NOTE: 'not' as unary operator is mutated in
         `unary_operator_replacement.py`, including deletion of the same
         operator.
    """
    NODE_TYPES = (parso.python.tree.IfStmt, parso.python.tree.WhileStmt,
                  parso.python.tree.AssertStmt)

    def mutation_positions(self, node):
        if isinstance(node, self.NODE_TYPES):
            expr = node.children[1]
            yield (expr.start_pos, expr.end_pos)
        elif isinstance(node,
                        parso.python.tree.PythonNode) and node.type == 'test':
            # ternary conditional
            expr = node.children[2]
            yield (expr.start_pos, expr.end_pos)

    def mutate(self, node, index):
        assert index == 0

        if isinstance(node, self.NODE_TYPES):
            expr_node = node.children[1]
            mutated_code = ' not{}'.format(expr_node.get_code())
            mutated_node = parso.parse(mutated_code)
            node.children[1] = mutated_node

        else:
            assert node.type == 'test'
            expr_node = node.children[2]
            mutated_code = ' not{}'.format(expr_node.get_code())
            mutated_node = parso.parse(mutated_code)
            node.children[2] = mutated_node

        return node

    @classmethod
    def examples(cls):
        return (
            ('if True or False: pass', 'if not True or False: pass'),
            ('A if B else C', 'A if not B else C'),
            ('assert isinstance(node, ast.Break)', 'assert not isinstance(node, ast.Break)'),
            ('while True: pass', 'while not True: pass'),
        )
