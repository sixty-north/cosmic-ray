[![Build Status](https://travis-ci.org/sixty-north/cosmic-ray.png?branch=master)](https://travis-ci.org/sixty-north/cosmic-ray) [![Code Health](https://landscape.io/github/sixty-north/cosmic-ray/master/landscape.svg?style=flat)](https://landscape.io/github/sixty-north/cosmic-ray/master)

# Cosmic Ray: mutation testing for Python

*"Four human beings -- changed by space-born cosmic rays into something more than merely human."*  
*— The Fantastic Four*

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
python setup.py install
cosmic-ray run my_module path/to/tests
```

This will print out a bunch of information about what Cosmic Ray is
doing, including stuff about what kinds of mutants are being created,
which were killed, and – chillingly – which survived.

## Installing and running Cosmic Ray

To install Cosmic Ray, just use the supplied `setup.py`:
```
python setup.py install
```

This will install the Cosmic Ray package and create an executable
called `cosmic-ray`.

(PyPI installation should be coming soon.)

Once installed, you can run `cosmic-ray` to get it a useful help
message:
```
cosmic-ray -h
```

The primary way of running `cosmic-ray` is by passing the `run`
command-line argument. With this command you tell Cosmic Ray a) which
module(s) you with to mutate and b) the location of the test
suite. For example, if you've a package named `allele` and if the
`unittest` tests for the package are all under the directory
`allele_tests`, you would run `cosmic-ray` like this:
```
cosmic-ray allele allele_tests
```

There are a number of other options you can pass to the `run` command;
see the help message for more details.

### Running with a config file

For many projects you'll probably be running the same `cosmic-ray`
command over and over. Instead of having to remember and retype
potentially complex commands each time, you can store `cosmic-ray`
commands in a config file. You can then execute these command by
passing the `load` command to `cosmic-ray`.

Each line in the config file is treated as a separate command-line
argument to `cosmic-ray`. Empty lines in the file are skipped, and you
can have comments in config file that start with `#`.

So, for example, if you need to invoke this command for your project:
```
cosmic-ray run --verbose --timeout=30 --no-local-import allele allele/tests/unittests
```

you could instead create a config file, `cr-allele.conf`, with these
contents:
```
run
--verbose
--timeout=30
--no-local-import
allele
allele/tests/unittests
```

Then to run the command in that config file:
```
cosmic-ray load cr-allele.conf
```

## Tests

Cosmic Ray has a number of test suites to help ensure that it works. The
first suite is a standard `unittest` test suite that validates some if
its internals. You can run that like this:

```
python -m unittest discover cosmic_ray/tests
```

There is also a set of tests which verify the various mutation
operators. These tests comprise a specially prepared body of code,
`adam.py`, and a full-coverage test-suite. The idea here is that
Cosmic Ray should be 100% lethal against the mutants of `adam.py` or
there's a problem. Run these tests like this:

```
cd test_project
cosmic-ray load cosmic-ray.conf
```

## Theory

Mutation testing is conceptually simple and elegant. You make certain
kinds of controlled changes (mutations) to your code, and then you
run your test suite over this mutated code. If your test suite fails,
then we say that your tests "killed" (i.e. detected) the mutant. If
the changes cause your code to simply crash, then we say the mutant is
"incompetent". If your test suite passes, however, we say that the
mutant has "survived".

Needless to say, we want to
[kill all of the mutants](http://www.troll.me/images/x-all-the-things/kill-all-the-mutants.jpg).

The goal of mutation testing is to verify that your test suite is
actually testing all of the parts of your code that it needs to, and
that it is doing so in a meaningful way. If a mutant survives your
test suite, this is an indication that your test suite is not
adequately checking the code that was changed. This means that either
a) you need more or better tests or b) you've got code which you don't
need.

You can read more about mutation testing at
[the repository of all human knowledge](http://en.wikipedia.org/wiki/Mutation_testing). Lionel
Brian has a
[nice set of slides](http://www.uio.no/studier/emner/matnat/ifi/INF4290/v10/undervisningsmateriale/INF4290-Mutest.pdf)
introducing mutation testing as well.

## Implementation

Cosmic Ray works by parsing the module under test (MUT) and its
submodules into a abstract syntax trees using
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

Cosmic Ray uses the
[multiprocessing module](https://docs.python.org/3/library/multiprocessing.html)
to run the tests in parallel and also to implement mutant
sandboxing. This provides a nice speed-up in many cases, though if your
tests are IO bound or use other common resources then this could
actually slow things down.
