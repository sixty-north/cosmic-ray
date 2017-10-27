# Implementation

Cosmic Ray works by parsing the module under test (MUT) and its
submodules into abstract syntax trees using
[the `ast` module](https://docs.python.org/3/library/ast.html). It
then uses
[the `ast.NodeTransformer` class](https://docs.python.org/3/library/ast.html#ast.NodeTransformer)
to make systematic mutations to the ASTs.

For each individual mutation, Cosmic Ray modifies the Python runtime
environment to replace the MUT with the mutated version. It then uses
[`unittest`'s "discovery" functionality](https://docs.python.org/3/library/unittest.html#test-discovery)
to discover your tests and run them against the mutant code.

In effect, the mutation testing algorithm is something like this:

```python
for mod in modules_under_test:
    for op in mutation_operators:
        for site in mutation_sites(op, mod):
            mutant_ast = mutate_ast(op, mod, site)
            replace_module(mod.name, compile(mutant_ast)

            try:
                if discover_and_run_tests():
                    print('Oh no! The mutant survived!')
                else:
                    print('The mutant was killed.')
            except Exception:
                print('The mutant was incompetent.')
```

Obviously this can result in a lot of tests, and it can take some time
if your test suite is large and/or slow.
