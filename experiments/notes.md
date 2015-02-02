We need to figure out how to run tests against modified ASTs. That is,
given an AST with mutated nodes, how do we run a suite of tests
against it.

It seems that we can generate Python source code from ASTs using
Ronacher's generator. Or we could roll our own; it's not too
complex. Given the source we could eval() it, but that doesn't give us
a module object. We could write it out to a tempfile and __import__()
it, dynamically replacing entries in the module table.

Assuming we can dynamically replace modules, the next question is how
we subsequently run tests that *use* that updated module. I guess the
central question for this experiment is whether
TestLoader().discover() will load tests in such a way that they use
the latest entries in the module table.

So, the experiment:

1. Write a simple TestCase that imports a module and runs a test using a
function from that module.

2. Write the source for that module and function to a tempfile, then load
that tempfile via __import__ (or other, more appropriate function) and
update the module dict with the module object. The source in this case
should be a version of the function for which the tests pass.

3. Use autodiscovery to run the TestCase and see that it passes.

4. Repeat (2), but this time the source code should such that the
   tests will fail.

5. Repeat (3) and see that the test(s) fail. If so, then it seems
   we've found a way to dynamically update modules in a way suitable
   for unittest test discovery!


Results: Test discovery reimportation
-------------------------------------

It appears that unittest test discovery will indeed respond properly
to module reloading. That is, if I import a module `mod`, use test
discovery to run some tests using that module, modify and reload
 `mod`, and then rediscover/run the tests, the second run of the tests
will be using the modified version of the module.

This means that we can now focus on modification of modules via AST
manipulation.

How can we (re)load modules from modified ASTs?
-----------------------------------------------


A few options seem open.

First, we could create a temporary directory wherein we write the
source code for the module(s). The we could arrange (via sys.path or
whatever appropriate mechanism) to import from there. When we modify
the AST we would just need to write the new source into that same
directory and use importlib.reload().

Since we build an AST by simply reading files and *not* by importing,
this might work. That is, we won't need to do an initial import of a
module to get its AST.

This approach may be slow, though. It will involve a good deal of file
IO, and this could be prohibitive for large projects. We would need to
rewrite the modules for each mutation operation at each possible
location. This could be 10s of thousands of times, or more...it would
be interesting to try estimating this.

(PyFakeFS might allow us to do this more quickly...I'm not sure.)

An alternative approach is to somehow replace the module without
needing to write files to disk. We would need some way to directly
update modules from the AST, bypassing fileio. Perhaps the elements of
the importlib loader system can help us here. I.e. analogous to the
ZIP loader, maybe we can make an "ASTLoader". This is a really
interesting idea! This will require quite some research.

Reimporting via importlib, loaders, etc.
----------------------------------------

It looks like we need to implement
[finder](https://docs.python.org/3/reference/import.html#finders-and-loaders]. This
gets a chance to say if it knows how to create a loader for a
specified module. We need to install this on `sys.meta_hook`.

It's legitimate to clear elements out of `sys.modules`, something we
should probably do prior to re-importing modules.

We'll also need to implement a
[loader](https://docs.python.org/3/reference/import.html#loaders). This
is the thing that actually creates the module contents. Here's the
[API for loaders](https://docs.python.org/3/library/importlib.html#importlib.abc.Loader).

Perhaps we can use [ResourceLoader](https://docs.python.org/3/library/importlib.html#importlib.abc.ResourceLoader).
