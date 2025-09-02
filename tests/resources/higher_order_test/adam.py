"""A simple module for testing higher-order mutations."""


def add_and_compare(a, b, c):
    """Add two numbers and compare with a third.

    This function contains multiple mutation opportunities:
    1. Arithmetic operator replacement (+ to -, *, /, etc.)
    2. Comparison operator replacement (> to <, ==, etc.)
    """
    result = a + b
    if result > c:
        return "Greater"
    elif result < c:
        return "Less"
    else:
        return "Equal"


def check_logic(x, y):
    """Test function with logic operations.

    This function contains multiple mutation opportunities in logical operators.
    """
    if x and y:
        return "Both"
    elif x or y:
        return "At least one"
    else:
        return "None"
