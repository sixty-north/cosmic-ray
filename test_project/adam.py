# A set of function which exercise specific mutation operators. This
# is paired up with a test suite. The idea is that cosmic-ray should
# kill every mutant when that suite is run; if it doesn't, then we've
# got a problem.


def constant_number():
    return 42


def unary_sub():
    return -1


def unary_add():
    return +1


def equals(vals):
    def constraint(x, y):
        return (x == y) ^ (x != y)

    return all([constraint(x, y)
                for x in vals
                for y in vals])


def use_break(limit):
    for x in range(limit):
        break
    return x


def use_continue(limit):
    for x in range(limit):
        continue
    return x
