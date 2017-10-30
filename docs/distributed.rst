Distributed testing with Celery
===============================

TODO: This needs to be reworked in light of the "execution engine"
concept, esp. once we make those into plugins.

One of the main practical challenges to mutation testing is that it can
take a long time. Even on moderately sized projects, you might need
millions of individual mutations and test runs. This can be prohibitive
to run on a single system.

One way to cope with these long runtimes is to parallelize the mutation
and testing procedures. Fortunately, mutation testing is `embarassingly
parallel in
nature <https://en.wikipedia.org/wiki/Embarrassingly_parallel>`__, so we
can apply some relatively simple techniques to get really nice scaling
up of the work. We've chosen to use the `Celery distributed task
queue <http://www.celeryproject.org/>`__ to spread work across multiple
nodes.

The basic idea is very simple. Celery lets you start multiple *workers*
which listen for commands from a task queue. A central process creates
all of the commands for a mutation testing run, and these commands are
distributed to the workers as they become available. When a worker
receives a command, it starts a *new* python process (using the
``worker`` subcommand to Cosmic Ray) which performs a single mutation
and runs the test suite.

Spawning a separate process for each test suite may seem expensive.
However, it's the best way we have for ensuring that pathological
mutants can't somehow corrupt the runtime of the worker processes. And
ultimately the cost of starting the process is likely to be very small
compared to the runtime of the test suite.

By its nature, Celery lets you start workers on as many systems as you
want, all connected to the same task queue. So you could potentially
have thousands of workers performing mutation testing runs, giving
nearly perfect scaling! While not everyone has thousands of machines on
hand to do their testing work, it's conceivable that Cosmic Ray will one
day be able to work with machines on commodity cloud providers, meaning
that highly-scaled mutation testing for Python will be available to
anyone who wants it.

Installing RabbitMQ
-------------------

Celery is primarily a Python API atop the
`RabbitMQ <https://www.rabbitmq.com/>`__ task queue. As such, if you
want to use Cosmic Ray in distributed mode you first need to install
RabbitMQ and run the server. The steps for installing and running
RabbitMQ are covered in detail at that project's site, so go there for
more information. Make sure the RabbitMQ server is installated and
running before going any further with distributed execution.

Starting distributed worker processes
-------------------------------------

Once RabbitMQ is running, you need to start some worker processes which
will do the actually mutation testing. Start one or more worker processes
like this:

::

    celery -A cosmic_ray.tasks.worker worker

You should do this, of course, from the virtual environment into which
you've installed Cosmic Ray. Similarly, you need to make sure that the
worker is in an environment in which it can import the modules under
test. Generally speaking, you can meet both of these criteria if you
install Cosmic Ray into and run workers from a virtual environment into
which you've installed the modules under test.

Running distributed mutation testing
------------------------------------

After you've started your workers, the only different between local and
distributed testing is that you need to pass ``--dist`` to the
``cosmic-ray exec`` command to do distributed testing. So a full
distributed testing run would look something like this:

::

    cosmic-ray init --baseline=3 session-name my_module -- tests
    cosmic-ray exec --dist session-name
    cosmic-ray report session-name
