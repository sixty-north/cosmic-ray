import re

_re_camel_to_kebab_case = re.compile(r'([0-9a-z])([A-Z])')


def to_kebab_case(s: str) -> str:
    """
    Convert from CamelCase or snake_case (or mixed) to kebab-case.

    >>> to_kebab_case('AbcDefGhi')
    'abc-def-ghi'
    >>> to_kebab_case('abcDefGhi')
    'abc-def-ghi'
    >>> to_kebab_case('abc_def_ghi')
    'abc-def-ghi'
    >>> to_kebab_case('abcDef_ghi')
    'abc-def-ghi'
    """
    s = s.replace('_', '-')
    return _re_camel_to_kebab_case.sub(r'\1-\2', s).lower()
