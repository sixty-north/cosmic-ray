"""
-----------
Simple Math
-----------

A set of simple math functions.
This is paired up with a test suite and intended to be run with cosmic-ray.
The idea is that cosmic-ray should kill every mutant when that suite is run;
if it doesn't, then we've got a problem.
"""


def mult_by_2(x):
    return x + x


def square(x):
    return x*x


def cube(x):
    return x*x*x


def is_positive(x):
    return x > 0
