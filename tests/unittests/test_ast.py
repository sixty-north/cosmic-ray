from cosmic_ray.ast import ast_nodes, get_ast_from_path
from cosmic_ray.ast.ast_query import ASTQuery


def test_call_get_ast_from_path(tmp_path):
    module_filepath = tmp_path / "module.py"
    input_code = "def foo():\n    pass\n"
    module_filepath.write_text(input_code)
    ast = get_ast_from_path(module_filepath)
    assert ast.get_code() == input_code


def _definition_names_from_source(tmp_path, source):
    """Parse source and return definition names for all AST nodes."""
    module_path = tmp_path / "module.py"
    module_path.write_text(source)
    module_ast = get_ast_from_path(module_path)
    return [ASTQuery(node).get_definition_name() for node in ast_nodes(module_ast)]


def test_get_definition_name_lambda_inside_function(tmp_path):
    source = "def foo():\n    xs = sorted(xs, key=lambda x: x)\n"
    names = _definition_names_from_source(tmp_path, source)
    assert "foo" in names
    assert all(n in ("foo", None) for n in names)


def test_get_definition_name_lambda_at_module_level(tmp_path):
    source = "f = lambda x: x + 1\n"
    names = _definition_names_from_source(tmp_path, source)
    assert all(n is None for n in names)


def test_get_definition_name_lambda_inside_class(tmp_path):
    source = "class Bar:\n    fn = lambda self: self\n"
    names = _definition_names_from_source(tmp_path, source)
    assert "Bar" in names
    assert all(n in ("Bar", None) for n in names)


def test_call_get_ast_from_path_with_non_utf8_encoding(tmp_path):
    module_filepath = tmp_path / "module.py"
    input_code = """# -*- coding: latin-1 -*-
def foo():
    pass
""".encode("latin-1")
    with module_filepath.open("wb") as f:
        f.write(input_code)
    ast = get_ast_from_path(module_filepath)
    assert ast.get_code().encode("latin-1") == input_code
