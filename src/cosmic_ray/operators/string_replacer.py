import parso
import sys
from parso.python.tree import PythonNode, Name, String, Module, Function, \
    FStringStart
from parso.tree import Node

from cosmic_ray.ast import is_string
from cosmic_ray.operators.operator import Operator
from cosmic_ray.operators.util import ASTQuery


class StringReplacer(Operator):
    """An operator that modifies numeric constants."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filtered_functions = set(self.config.get('filter-if-called-by', ()))
        self.replace_with = self.config.get('replace-with', "COSMIC %s RAY")

    def mutation_positions(self, node: Node):
        # _("abc"):
        # gives
        # [
        #     Name('_'),
        #     PythonNode('trailer', [
        #         Operator('('),
        #         Name('abc'),  <-- node
        #         Operator(')'),
        #     ]),
        # ]

        # self.tr("abc") gives:
        # [
        #     PythonNode('atom_expr', [
        #         Name('self'),
        #         PythonNode('trailer', [
        #             Operator('.'),
        #             Name('tr')
        #         ]),
        #         PythonNode('trailer', [
        #             Operator('('),
        #             Name('abc'),  <-- node
        #             Operator(')'),
        #         ]),
        #     ]),
        # ]

        if is_string(node) and not self._is_docstring(node):
            if self.filtered_functions:
                if ASTQuery(node).parent. \
                        IF.match(PythonNode, type='fstring').parent.FI. \
                        match(PythonNode, type='trailer'). \
                        get_previous_sibling(). \
                        IF.match(PythonNode, type='trailer').children[-1].FI. \
                        match(Name, value__in=self.filtered_functions).ok:
                    return

            yield node.start_pos, node.end_pos

    @classmethod
    def _is_docstring(cls, node):
        return cls._is_module_docstring(node) or \
               cls. _is_function_docstring(node)

    @staticmethod
    def _is_module_docstring(node):
        """
        Module(file_input, [
            PythonNode(simple_stmt, [  <-- or not
                String(string, '"Doc string"'),
            ]),
        ])
        """
        return ASTQuery(node).match(String). \
            IF.parent.match(PythonNode, type='simple_stmt').FI. \
            parent.match(Module).ok

    @staticmethod
    def _is_function_docstring(node):
        """
        Function(funcdef, [
            Keyword(keyword, 'def'),
            Name(name, 'f'),
            PythonNode(parameters, [...]),
            Operator(operator, ':'),
            PythonNode(suite, [
                Newline(newline, '\n'),
                PythonNode(simple_stmt, [  <-- or not
                    String(string, '"doc"'),  <-- node
                    Newline(newline, '\n'),
                ]),
            ]),
        ]),
        """
        return ASTQuery(node).match(String). \
            IF.parent.match(PythonNode, type='simple_stmt').FI. \
            parent.match(PythonNode, type='suite'). \
            parent.match(Function).ok

    def mutate(self, node, index):
        """Modify the numeric value on `node`."""
        if isinstance(node, String):
            s = node.value
            if s.endswith(("'''", '"""')):
                enclose_end = 3
            else:
                enclose_end = 1
            enclose_start = enclose_end
            if s.startswith(('r', 'b', 'u')):
                enclose_start += 1

            new_s = self.replace_with % s[enclose_start:-enclose_end]
            node.value = '%s%s%s' % (s[:enclose_start], new_s, s[-enclose_end:])
            return node

        elif isinstance(node, FStringStart):
            s = ''.join(n.get_code() for n in node.parent.children[1:-1])
            s = self.replace_with % s
            s = '%s%s%s' % (node.value, s, node.parent.children[-1].value)
            node.parent.children[:] = parso.parse(s).children[0].children
            return node

        else:
            raise ValueError("Node can't be of type {}".format(type(node).__name__))

    @classmethod
    def examples(cls):
        config = {
            'replace-with': 'XX %s',
            'filter-if-called-by': ['_', 'tr'],
        }
        data = [
            ('s = "abc"', 's = "XX abc"', 0, config),
            ('s = """abc"""', 's = """XX abc"""', 0, config),
            ("s = '''abc'''", "s = '''XX abc'''", 0, config),

            ('s = r"abc"', 's = r"XX abc"', 0, config),
            ('s = r"""abc"""', 's = r"""XX abc"""', 0, config),
            ("s = r'''abc'''", "s = r'''XX abc'''", 0, config),

            ('s = b"abc"', 's = b"XX abc"', 0, config),
            ('s = b"""abc"""', 's = b"""XX abc"""', 0, config),
            ("s = b'''abc'''", "s = b'''XX abc'''", 0, config),

            ('s = u"abc"', 's = u"XX abc"', 0, config),
            ('s = u"""abc"""', 's = u"""XX abc"""', 0, config),
            ("s = u'''abc'''", "s = u'''XX abc'''", 0, config),


            ('f("abc")', 'f("XX abc")', 0, config),
            ('_("abc")', '_("abc")', 0, config),
            ('self.tr("abc")', 'self.tr("abc")', 0, config),
            ('"Module doc string"', '"Module doc string"', 0, config),
            ('def f():\n    "Function doc string"',
             'def f():\n    "Function doc string"', 0, config),
        ]

        if sys.version_info >= (3, 6):
            # Adding fstring
            data += [
                ('s = f"abc"', 's = f"XX abc"', 0, config),
                ('s = f"abc {1} def"', 's = f"XX abc {1} def"', 0, config),
            ]

        return data
