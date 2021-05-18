Theory
======

Mutation testing is conceptually simple and elegant. You make certain kinds of controlled changes (mutations) to your
*code under test* [1]_, and then you run your test suite over this mutated code. If your test suite fails, then we say that
your tests "killed" (i.e. detected) the mutant. If the changes cause your code to simply crash, then we say the mutant
is "incompetent". If your test suite passes, however, we say that the mutant has "survived".

Needless to say, we want to kill all of the mutants.

The goal of mutation testing is to verify that your test suite is
actually testing all of the parts of your code that it needs to, and
that it is doing so in a meaningful way. If a mutant survives your test
suite, this is an indication that your test suite is not adequately
checking the code that was changed. This means that either a) you need
more or better tests or b) you've got code which you don't need.

You can read more about mutation testing at `the repository of all human
knowledge <https://en.wikipedia.org/wiki/Mutation_testing>`__. Lionel
Brian has a `nice set of
slides <http://www.uio.no/studier/emner/matnat/ifi/INF4290/v10/undervisningsmateriale/INF4290-Mutest.pdf>`__
introducing mutation testing as well.

.. [1] By "code under test", we mean the code that your test suite is testing. Mutation testing is trying
       to ensure that your unaltered test suite can detect explicitly incorrect behavior in your code.

