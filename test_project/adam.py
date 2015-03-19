# A set of function which exercise specific mutation operators. This
# is paired up with a test suite. The idea is that cosmic-ray should
# kill every mutant when that suite is run; if it doesn't, then we've
# got a problem.


def unary_sub():
    return -1


def unary_add():
    return +1


def equals():
    def constraint(x, y):
        (x == y) ^ (x != y)

    vals = [1, 2, 3]

    return all([constraint(x, y)
                for x in vals
                for y in vals])
