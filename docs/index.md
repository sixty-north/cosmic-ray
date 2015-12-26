# Cosmic Ray: mutation testing for Python

*"Four human beings -- changed by space-born cosmic rays into something more than merely human."*  
*— The Fantastic Four*

Cosmic Ray is a tool for performing mutation testing on Python
code.

## N.B.! Cosmic Ray is still learning how to walk!

At this time Cosmic Ray is young and incomplete. It doesn't support
all of the mutations it should, its output format is crude, it only
supports some forms of test discovery, it may fall over on exotic
modules...[the list goes on and on](https://github.com/sixty-north/cosmic-ray/issues). Still,
for the adventurous it *does* work. Hopefully things will improve
fairly rapidly.

And, of course, patches and ideas are welcome.

## Quickstart

If you just want to get down to the business of finding and killing
mutants, here's what you do:

1. Install Cosmic Ray

```
pip install cosmic_ray
```

2. Install and start RabbitMQ

3. Start a Cosmic Ray worker task

```
celery -A cosmic_ray.worker worker
```

4. Run the top-level Cosmic Ray task manager

```
cosmic-ray run --baseline=10 <module name> <test directory>
```

This will print out a bunch of information about what Cosmic Ray is
doing, including stuff about what kinds of mutants are being created,
which were killed, and – chillingly – which survived.

## Installation

You can install Cosmic Ray using `pip`:

```
pip install cosmic_ray
```

Or you can use the supplied `setup.py`:

```
python setup.py install
```

Both of these approaches will install the Cosmic Ray package and
create an executable called `cosmic-ray`.

### Virtual environments

You'll often want to install Cosmic Ray into a virtual environment. However, you
generally *don't* want to install it into its own. Rather, you want to install
it into the virtual environment of the project you want to test. This ensure
that the workers have access to the modules they are supposed to test.

### Installing RabbitMQ

Cosmic Ray uses [Celery](http://www.celeryproject.org/) to distribute tasks to
workers, and currently we only support the [RabbitMQ](https://www.rabbitmq.com/)
backend of Celery. So you need to install RabbitMQ onto your system. This should
be straightforward.

Once installed, make sure to start the RabbitMQ server.

## Running Cosmic Ray

Once RabbitMQ is running, you need to start one or more worker tasks. These are
started using the `celery` command, and these workers listen for testing
instructions from the Cosmic Ray executive level. You can have as many workers
as you want, and they can be on multiple machines (in principle...we don't
really support that as of this writing).

Start worker processes like this:

```
celery -A cosmic_ray.worker worker
```

You should do this, of course, from the virtual environment into which you've
installed Cosmic Ray.

Once you've got some workers running, you can make them do work by passing the
`run` command-line argument. With this command you tell Cosmic Ray a) which
module(s) you wish to mutate and b) the location of the test suite. For example,
if you've a package named `allele` and if the `unittest` tests for the package
are all under the directory `allele_tests`, you would run `cosmic-ray` like
this:

```
cosmic-ray run --baseline=2 allele allele_tests
```

There are a number of other options you can pass to the `run` command;
see the help message for more details.

### Test runners

Cosmic Ray supports multiple *test runners*. A test runner is simply a
plugin that supports a particular way of running tests. For example,
there is a test runner for tests written with the standard `unittest`
module, and there's another for tests written using
[`py.test`](pytest.org).

To specify a particular test runner when running Cosmic Ray, pass the
`--test-runner` flag to the `run` subcommand. For example, to use the
`pytest` runner you would use:
```
cosmic-ray run --test-runner=pytest allele allele_tests
```

To get a list of the available test runners, use the `test-runners`
subcommand:
```
cosmic-ray test-runners
```

### Specifying test timeouts

**TODO:** Update this once timeouts are re-implemented.

One difficulty mutation testing tools have to face is how to deal with
mutations that result in infinite loops (or other pathological runtime
effects). Cosmic Ray takes the simple approach of using a *timeout* to
determine when to kill a test and consider it *incompetent*. That is,
if a test of a mutant takes longer than the timeout, the test is
killed an the mutant is marked incompetent.

There are two ways to specify timeout values to Cosmic Ray. The first
is through the `--timeout` flag for the `run` subcommand. This flags
specifies an absolute number of seconds that a test will be allowed to
run. After the timeout is up, the test is killed. For example, to
specify that tests should timeout after 10 seconds, use:
```
cosmic-ray run --timeout=10 allele allele/tests
```

The second way is by using a baseline timing. To use this technique,
pass the `--baseline` argument to the `run` subcommand. When Cosmic
Ray sees this flag it will make an initial run of the tests on an
un-mutated version of the module under test. The amount of time this
takes is considered the *baseline timing*. Then, Cosmic Ray multiplies
this baseline timing by the value of `--baseline` and this final value
is used as the timeout for tests. For example, to tell Cosmic Ray to
timeout tests when they take 3 times longer than a baseline run, use:
```
cosmic-ray run --baseline=3 allele allele/tests
```

This baseline technique is particularly useful if your testsuite
runtime is in flux.

### Running with a config file

**TODO:** Update this once we settle the celery implementation down. In
  particular, make it clear that you still need to start workers, etc.

For many projects you'll probably be running the same `cosmic-ray`
command over and over. Instead of having to remember and retype
potentially complex commands each time, you can store `cosmic-ray`
commands in a config file. You can then execute these commands by
passing the `load` command to `cosmic-ray`.

Each line in the config file is treated as a separate command-line
argument to `cosmic-ray`. Empty lines in the file are skipped, and you
can have comments in config files that start with `#`.

So, for example, if you need to invoke this command for your project:

```
cosmic-ray run --verbose --timeout=30 --no-local-import --baseline=2 allele allele/tests/unittests
```

you could instead create a config file, `cr-allele.conf`, with these
contents:

```
run
--verbose     # this can be useful for debugging
--timeout=30  # this is plenty of time
--no-local-import
--baseline=2
allele
allele/tests/unittests
```

Then to run the command in that config file:

```
cosmic-ray load cr-allele.conf
```

and it will have the same effect as running the original command.

## Tests

**TODO:** Update this once teh celery implementation is more complete.

Cosmic Ray has a number of test suites to help ensure that it works. The
first suite is a standard `unittest` test suite that validates some if
its internals. You can run that like this:

```
python -m unittest discover cosmic_ray/test
```

There is also a set of tests which verify the various mutation
operators. These tests comprise a specially prepared body of code,
`adam.py`, and a full-coverage test-suite. The idea here is that
Cosmic Ray should be 100% lethal against the mutants of `adam.py` or
there's a problem.

These tests can be run via both the standard `unittest` and `py.test`. In both
cases, first go to the `test_project` directory:

```
cd test_project
```

Run the operator tests with `unittest` like this:

```
cosmic-ray load cosmic-ray.unittest.conf
```

and with `py.test` like this:

```
cosmic-ray load cosmic-ray.pytest.conf
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

**TODO:** Add information about how we use celery.
