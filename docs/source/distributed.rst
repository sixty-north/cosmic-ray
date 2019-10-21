==============================
 Distributed mutation testing
==============================

One of the main practical challenges to mutation testing is that it can
take a long time. Even on moderately sized projects, you might need
millions of individual mutations and test runs. This can be prohibitive
to run on a single system.

One way to cope with these long runtimes is to parallelize the mutation and
testing procedures. Fortunately, mutation testing is `embarassingly parallel in
nature <https://en.wikipedia.org/wiki/Embarrassingly_parallel>`__, so we can
apply some relatively simple techniques to get really nice scaling up of the
work. To support parallel execution of mutation testing runs, Cosmic Ray has the
notion of *execution engines* which can control where and how tests are run.
Different engines can run tests in different contexts: in parallel on a single
machine, by distributing them across a message bus, or perhaps by spawning test
runs on cloud systems.

**THIS SECTION SHOULD BE CONSIDERED OUT OF DATE UNTIL FURTHER NOTICE.**
We will reimplement celery support, but right now it's probably broken.

The Celery execution engine
===========================

The Cosmic Ray repository includes the `celery4` execution engine. This is
provided as a plugin via the `cosmic_ray_celery4_engine` package in the
`plugins/execution_engines/celery3` directory. This engine uses the `Celery
distributed task queue <http://www.celeryproject.org/>`__ to spread work across
multiple nodes. (It's called "celery4" since it uses version 4 of Celery;
version 4 will be available at some point as well).

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

Installing the `celery4` worker
-------------------------------

The `cosmic_ray_celery34engine` package is installed separately from
`cosmic_ray` itself. This is primarily so that `cosmic_ray` doesn't have a
direct dependency on any version of `celery`.

To install the plugin, you need to run this command from `plugins/execution-engines/celery4`:

::

    python setup.py install

This will install and register the plugin.

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

    celery -A cosmic_ray_celery4_engine.worker worker

You should do this, of course, from the virtual environment into which
you've installed Cosmic Ray. Similarly, you need to make sure that the
worker is in an environment in which it can import the modules under
test. Generally speaking, you can meet both of these criteria if you
install Cosmic Ray into and run workers from a virtual environment into
which you've installed the modules under test.

.. _running_distributed_mutation_testing:

Running distributed mutation testing
------------------------------------

Aside from starting workers, you also need to specify `celery4` in your
configuration. For example, instead of a "local" configuration like this:

::

    execution-engine.name = "local"

You would use the name "celery4" like this:

::

    execution-engine.name = "celery4"

With this configuration in place, you then need to do an `init` to create a
session followed by `exec` to run the tests:

::

    cosmic-ray init my_config my_session
    cosmic-ray exec my_session

This `exec` will distribute testing runs to your celery workers.
