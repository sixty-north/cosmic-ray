from parso.python.tree import PythonNode, Function, ReturnStmt, \
    Operator as tree_Operator
from parso.tree import Node

from cosmic_ray.interceptors import Interceptor
from cosmic_ray.operators.operator import Operator
from cosmic_ray.operators.util import ASTQuery
from cosmic_ray.work_item import WorkItem, WorkerOutcome


class AnnotationInterceptor(Interceptor):
    """
    Filter all keyword inside annotation:
    Example 'or' inside following sentence must be skipped for mutation
    >>> a: int or float = None
    >>> def f(a: int or float): pass
    >>> def g(a) -> int or float: pass
    """

    def post_add_work_item(self,
                          operator: Operator,
                          node: Node,
                          work_item: WorkItem):

        if self._is_var_annotation(node):
            self._add_work_result(
                work_item,
                output="Skipped by annotation interceptor",
                worker_outcome=WorkerOutcome.SKIPPED,
            )

    @staticmethod
    def _is_var_annotation(node):
        """
        a: int or float = 1 or 2

        ExprStmt(expr_stmt, [
            Name(name, 'a'),

            PythonNode(annassign, [         <-- if  (and loop guard)
  f(a: int):           PythonNode(tfpdef, [

                Operator(operator, ':'),    <-- and if ':' skip
                PythonNode(or_test, [
                    Name(name, 'int'),
                    Keyword(keyword, 'or'),  <-- node
                    Name(name, 'float'),
                ]),
                Operator(operator, '='),    <-- and if '=' pass
                PythonNode(or_test, [
                    Name(number, '1'),
                    Keyword(keyword, 'or'),  <-- node
                    Name(number, '2'),
                ]),
            ]),
        ]),
        """
        t = ASTQuery(node)
        while t:
            t_parent = t.parent
            if t_parent.match(PythonNode, type__in=('annassign', 'tfpdef')):
                # annassign: "a = x"
                # tfpdef: in "def f", parameter declaration list "a: int = 3"
                t_prev = t.get_previous_sibling().match(tree_Operator)
                if t_prev:
                    if t_prev.match(value=':'):
                        return True
                    elif t_prev.match(value='='):
                        return False
            elif t_parent.match(Function):
                # Function: def f() -> int:
                return t.get_previous_sibling().match(tree_Operator).match(value='->')
            t = t_parent

            # Loop guard
            # Don't explore over "=", "def ", "return"
            if t.match(PythonNode, type='annassign') or \
                t.match((Function, ReturnStmt)):
                return False
        return False
