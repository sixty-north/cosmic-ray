Implementation
==============

Cosmic Ray works by parsing the module under test (MUT) and its submodules into
abstract syntax trees using `parso <https://github.com/davidhalter/parso>`_. It
walks the parse trees produced by parso, allowing mutation operators to modify
or delete them. These modified parse trees are then turned back into code which
is written to disk for use in a test run.

For each individual mutation, Cosmic Ray modifies the Python runtime
environment to replace the MUT with the mutated version. It then uses
user-supplied test commands to run tests against mutated code.

In effect, the mutation testing algorithm is something like this:

.. code:: python

    for mod in modules_under_test:
        for op in mutation_operators:
            for site in mutation_sites(op, mod):
                mutant_ast = mutate_ast(op, mod, site)
                write_to_disk(mutant_ast)

                try:
                    if discover_and_run_tests():
                        print('Oh no! The mutant survived!')
                    else:
                        print('The mutant was killed.')
                except Exception:
                    print('The mutant was incompetent.')

Obviously this can result in a lot of tests, and it can take some time
if your test suite is large and/or slow.
