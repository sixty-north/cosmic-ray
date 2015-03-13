def get_line_number(node):
    """Try to get the line number for `node`.

    If no line number is available, this returns "<UNKNOWN>".
    """
    if hasattr(node, 'lineno'):
        return node.lineno
    else:
        return '<UNKNOWN>'
