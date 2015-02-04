# Cosmic Ray: mutation testing for Python

Cosmic Ray is a tool for performing mutation testing on Python
code.

## N.B.! Cosmic Ray is still learning how to walk!

At this time Cosmic Ray is young and incomplete. It doesn't support
all of the mutations it should, its output format is crude, it only
supports one kind of test discovery, it may fall over on exotic
modules...[the list goes on and on](https://github.com/abingham/cosmic-ray/issues). Still,
for the adventurous it *does* work. Hopefully things will improve
fairly rapidly.

And, of course, patches and ideas are welcome.

## Quickstart

If you just want to get down to the business of finding and killing
mutants, here's what you do:

```
% python -m cosmic_ray.app my_module path/to/tests
```

This will print out a bunch of information about what Cosmic Ray is
doing, including stuff about what kinds of mutants are being created,
which were killed, and – most frighteningly – which survived.

## Theory

Mutation testing is conceptually simple and elegant. You make certain
kinds of controlled changes (mutations) to your codebase, and then you
run your test suite over this mutated code. If your test suite fails,
then we say that your tests "killed" (i.e. detected) the mutant. If
the changes cause your code to simply crash, then we say the mutant is
"incompetent". If your test suite passes, however, we say that the
mutant has "survived".

Needless to say, we want to
[kill all of the (competent) mutants](http://www.troll.me/images/x-all-the-things/kill-all-the-mutants.jpg).

The goal of mutation testing is to verify that your test suite is
actually testing all of the parts of your code that it needs to, and
that it is doing so in a meaningful way. If a mutant survives your
test suite, this is an indication that your test suite is not
adequately checking the code that was changed. This means that either
a) you need more or better tests or b) you've got code which you don't
need.

You can read more about mutation testing at
[the repository of all human knowledge](http://en.wikipedia.org/wiki/Mutation_testing).

## Implementation

Cosmic Ray works by parsing the module under test (MUT) and its
submodules into a abstract syntax trees using
[the `ast` module](https://docs.python.org/3/library/ast.html). It
then uses
[the `ast.NodeTransformer` class](https://docs.python.org/3/library/ast.html#ast.NodeTransformer)
to make systematic mutations to the ASTs.

For each individual mutation, Cosmic Ray uses Python's low-level
[finder](https://docs.python.org/3/reference/import.html#finders-and-loaders)
and [loader](https://docs.python.org/3/reference/import.html#loaders)
system to dynamically replace the MUTs with the mutated versions. It
then uses
[`unittest`'s "discovery" functionality](https://docs.python.org/3/library/unittest.html#test-discovery)
to discover your tests and run them against the mutant code.

In effect, the mutation testing algorithm is something like this:

```
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
