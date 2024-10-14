from cosmic_ray.ast import get_ast_from_path


def test_call_get_ast_from_path(tmp_path):
    module_filepath = tmp_path / "module.py"
    input_code = "def foo():\n    pass\n"
    module_filepath.write_text(input_code)
    ast = get_ast_from_path(module_filepath)
    assert ast.get_code() == input_code


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
