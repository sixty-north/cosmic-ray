import re
from typing import Dict, List

_re_pragma = re.compile(r'([-A-Za-z0-9](?: (?! )|[-A-Za-z0-9])*)(:?)(,?)')


def get_pragma_list(line: str) -> None or Dict[str, None or List[str]]:
    """
    Pragma syntax:
    - Any comment can be present before 'pragma:' declaration
    - You can have multiple pragma family separated with double space
        (allowing family name having multiple words)
    - You can declare sections of pragma if the pragma name is followed
        directly with ':'
    - Pragma family can have an empty section set if no section is declared
        after ':'  ex "fam:" or "fam1:  fam2
    - Section names can have a space (two spaces indicate the end
        of section list)
    - Sections are separated with ',', comma directly present after the
        previous section (no space)

    :return Dictionary of list of sections per pragma family.
        If a pragma family have no section, the dictionary will returns None

    >>> get_pragma_list("# comment")
    None
    >>> get_pragma_list("# comment pragma:")
    {}
    >>> get_pragma_list("# comment pragma: x y  z")
    {'x y': None, 'z': None}
    >>> get_pragma_list("# comment pragma: x:")
    {'x': []}
    >>> get_pragma_list("# comment pragma: x:  y")
    {'x': [], 'y': None}
    >>> get_pragma_list("# comment pragma: x y  z: d, e")
    {'x y': None, 'z': ['d', 'e']}
    >>> get_pragma_list("# comment pragma: x: a, b, c  y z: d, e")
    {'x': ['a', 'b', 'c'], 'y z': ['d', 'e']}
    >>> get_pragma_list("comment pragma: x: a, b, c y  z: d, e")
    {'x': ['a', 'b', 'c y'], 'z': ['d', 'e']}
    """
    split = line.split('pragma:', maxsplit=1)
    if len(split) == 1:
        return None
    pragma_list = split[1]

    pragma = {}
    family_name = None
    last_section_pos = None
    for m in _re_pragma.finditer(pragma_list):
        elt = m.group(1)

        if family_name and m.start() > last_section_pos + 1:
            # The element is too far away, a new family is starting
            family_name = None

        if family_name:
            # If family_name in progress, add elt as section
            pragma[family_name].append(elt)
            if not m.group(3):
                # If no comma, next will be a key
                family_name = None
                last_section_pos = None
            else:
                last_section_pos = m.end()
        else:
            # No family_name in progress, elt is the family_name
            if m.group(2):
                # Followed by ':', next will be a section
                family_name = elt
                pragma[family_name] = []
                last_section_pos = m.end()
            else:
                # No ':', this family_name have no section,
                # next is another family_name
                pragma[elt] = None
    return pragma
