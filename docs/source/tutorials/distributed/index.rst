==================================================
Tutorial: Distributed, concurrent mutation testing
==================================================

One of the main practical challenges to mutation testing is that it can
take a long time. Even on moderately sized projects, you might need
millions of individual mutations and test runs. This can be prohibitive
to run on a single system.

One way to cope with these long runtimes is to parallelize the mutation and
testing procedures. Fortunately, mutation testing is `embarassingly parallel in
nature <https://en.wikipedia.org/wiki/Embarrassingly_parallel>`__, so we can
apply some relatively simple techniques to get really nice scaling up of the
work. To support parallel execution of mutation testing runs, Cosmic Ray has the
notion of *distributors* which can control where and how tests are run.
Different distributors can run tests in different contexts: in parallel on a single
machine, by distributing them across a message bus, or perhaps by spawning test
runs on cloud systems.

The HTTP distributor
====================

Cosmic Ray includes :class:`cosmic_ray.distributors.http.HttpDistributor`, a distributor which allows you to send
mutation-and-test requests to workers running locally or remotely. You can run as many of these workers as you 
want, thereby making it possible to run as many mutations in parallel as you want. 

Each worker is a small HTTP server, listening for requests from the ``exec`` command to perform a mutation and test. Each worker handlers
only one mutation request at a time. Critically, each worker has its own copy of the code under test, meaning that it can make mutations
to that copy of the code without interfering with other workers.

You need to make sure that workers are running prior to running the ``exec`` command. ``exec`` doesn't have any support
for starting workers. The major configuration involved with the HTTP distributor is telling ``exec`` where there workers
are listening.

A sample project
----------------

To demonstrate ``HttpDistributor`` we'll need a sample module and test suite. We'll use a very simple set
of code, as we did in :ref:`the basic tutorial <basic tutorial>`.

Create a new directory to hold this code. We'll refer to this directory as ``ROOT``.

Create the file ``ROOT/mod.py`` with these contents:

.. literalinclude:: mod.1.py

Then create ``ROOT/test_mod.py`` with these contents:

.. literalinclude:: test_mod.1.py

Finally, we'll create a configuration, ``ROOT/config.toml``:

.. literalinclude:: config.1.toml
    :linenos:

This config is similar to others that we've looked at, with the major difference that it specifies the use of the 'http'
distributor rather than 'local'. On line 8 we set "cosmic-ray.distributor.name" to "http". 

Then on line 11 we set the "cosmic-ray.distributor.http.worker-urls" setting to a list containing a URL. This is the
address at which a *worker* will be listening for mutation requests. This configuration only specifies a single worker,
but we can put as many workers here as we want.

Starting a worker
-----------------

Before Cosmic Ray can send requests to a worker, we need to start it. From the ``ROOT`` directory, start a worker using the
``http-worker`` command:

.. code-block:: bash

    cd $ROOT
    cosmic-ray --verbosity INFO http-worker --port 9876

The ``--verbosity INFO`` argument configures the worker's logging to show more messages than normal. The ``--port 9876``
argument instructs it to listen for requests on port 9876, the same port we specified in the 'worker-urls' list in our
configuration. The worker will tell you that it's waiting to process requests on port 9876:

.. code-block:: bash

    ======== Running on http://0.0.0.0:9876 ========
    (Press CTRL+C to quit)    

Note that your worker must be running in the same directory as you would normally run the tests from. In this case, we're
expecting the tests to be run in ``$ROOT``, so make sure your worker is running in that directory. Generally speaking,
the worker doesn't do much more than mutate the code on disk and run the test command you've specified in your config.

Running the tests
-----------------

We need to leave the worker running in its own terminal, so for these next steps you'll need to start a new terminal.

First we need to initialize a new Cosmic Ray session:

.. code-block:: bash

    cd $ROOT
    cosmic-ray init config.toml session.sqlite

Once the session is created, we can execute the tests:

.. code-block:: bash

    cosmic-ray exec config.toml session.sqlite

This should execute very quickly. The most important thing to note is that our worker process is where the mutation
and testing actually occurred. If you switch back to the terminal hosting your worker, you should see that it 
produced output something like this:

.. code-block:: bash

    [05/16/21 11:31:10] INFO     INFO:cosmic_ray.mutating:Applying mutation: path=mod.py,                                mutating.py:111
                                 op=<cosmic_ray.operators.number_replacer.NumberReplacer object at 0x10d2b9550>,                        
                                 occurrence=1                                                                                           
                        INFO     INFO:cosmic_ray.testing:Running test (timeout=10.0): python -m unittest test_mod.py       testing.py:36
                        INFO     INFO:aiohttp.access:::1 [16/May/2021:09:31:10 +0000] "POST / HTTP/1.1" 200 899 "-"       web_log.py:206
                                 "Python/3.7 aiohttp/3.7.4.post0"                                                                       
                        INFO     INFO:cosmic_ray.mutating:Applying mutation: path=mod.py,                                mutating.py:111
                                 op=<cosmic_ray.operators.number_replacer.NumberReplacer object at 0x10d4cdf60>,                        
                                 occurrence=0                                                                                           
                        INFO     INFO:cosmic_ray.testing:Running test (timeout=10.0): python -m unittest test_mod.py       testing.py:36
    [05/16/21 11:31:11] INFO     INFO:aiohttp.access:::1 [16/May/2021:09:31:10 +0000] "POST / HTTP/1.1" 200 899 "-"       web_log.py:206
                                 "Python/3.7 aiohttp/3.7.4.post0" 

Congratulations! You've just performed your first distributed mutation testing with Cosmic Ray. There are other details
you need to consider when scaling beyond a single worker, but this small example covers the most important elements:
setting up the configuration and starting a worker.

At this point you can kill the worker you started earlier.

Concurrent execution with multiple workers
==========================================

In the previous example we only ran a single worker process, so from a concurrency point of view this was no different from 
using the 'local' distributor. Before we can run multiple workers, though, we need to consider what resources each worker 
requires. Ultimately, each worker needs two things:

- An HTTP endpoint
- A copy of the code under test that it can modify

In this example we'll create the unique endpoints by giving each worker its own port. In principle, though, workers may be
running on entirely different machines on a network.

Distinct copies of the code
---------------------------

As mentioned earlier, Cosmic Ray mutation works by actually modifying the code on disk. As such, multiple workers can't
share a single copy of the code; their mutations would interfere with one another. So we need to make sure each worker
has a copy of the code under test.

For this example, we'll manually copy the files around:

.. code-block:: bash

    cd $ROOT
    mkdir worker1
    cp mod.py worker1
    cp test_mod.py worker1
    mkdir worker2
    cp mod.py worker2
    cp test_mod.py worker2

Now the directories ``worker1`` and ``worker2`` contain separate copies of the code under test.

Starting the workers
--------------------

Now we can start the workers. Remember that each will run in its own terminal. In one terminal, start the first worker:

.. code-block:: bash

    cd $ROOT/worker1
    cosmic-ray --verbosity INFO http-worker --port 9876

Then in another terminal start a second worker:

.. code-block:: bash

    cd $ROOT/worker2
    cosmic-ray --verbosity INFO http-worker --port 9877

Note that the workers are using different ports.

Update the configuration
------------------------

To tell Cosmic Ray to use both of these workers, we need to update our configuration. Edit ``config.toml`` to specify
both workers URLs:

.. literalinclude:: config.2.toml
    :linenos:
    :emphasize-lines: 11

On line 11 we now list the endpoints for both workers.

Running the tests
-----------------

We're now ready to run the tests. Go back to ``ROOT`` and re-initialize your session:

.. code-block:: bash

    cd $ROOT
    cosmic-ray init config.toml session.sqlite

Finally, we can execute the tests:

.. code-block:: bash

    cosmic-ray exec config.toml session.sqlite

If you run ``cr-report`` you should see that two tests were run and that there were no survivors:

.. code-block:: bash

    $ cr-report session.sqlite
    e4e56a71a059466f861d62c987988efe mod.py core/NumberReplacer 0
    worker outcome: normal, test outcome: killed
    7820da3f68cd40a7b60d69506e87c4aa mod.py core/NumberReplacer 1
    worker outcome: normal, test outcome: killed
    total jobs: 2
    complete: 2 (100.00%)
    surviving mutants: 0 (0.00%)

Likewise, if you look at the terminals for your two workers, you should see that they each received a request to perform
a mutation test.

That's really all there is to distributed mutation testing with ``HttpDistributor``. You simply start as many workers as you
need, specifying their endpoints in your configuration. 

.. important::

    At this point you should kill the workers you started.

cr-http-workers: A tool for starting workers
============================================

It's extremely common for the code under test (and the tests themselves) to be in a git repository. As such, a simple
way to create the isolated copies of the code that each worker requires is to clone this git repository. Once the
mutation testing is done, these clones can be deleted.

To simplify this process Cosmic Ray provides ``cr-http-workers``. This program reads your configuration to
determine how many workers to start, and you provide it with a git repository to clone. For each 'worker-url' in your
configuration it will clone the git repository and start a worker in that clone. You can then run ``exec`` to distribute
work to those workers. Once the testing is over, you can kill ``cr-http-workers`` and it will clean up the workers and
their clones.

Preparing the git repository
----------------------------

To use ``cr-http-workers`` we first need a git repository, so we'll create one from our existing code. 

.. note::

    You should first delete the ``worker1`` and ``worker2`` directories if they still exist. This isn't critical, but it
    might be confusing to leave them around.

Here's how to initialize the git repository:

.. code-block:: bash

    cd $ROOT
    git init
    git add mod.py 
    git add test_mod.py
    git commit -a -m "initialized repo"

Running the workers
-------------------

Once the git repo is initialized, we can start the workers:

.. code-block:: bash

    cr-http-workers config.toml .

This tell ``cr-http-workers`` to read ``config.toml`` to determine the worker endpoints. The second argument, ".", tells
it to clone the git repository in the current directory. In practice this repo URL will often be hosted elsewhere (e.g.
github), but for our purposes we'll just work with the local repo.

This will start both workers processes, and the output from those workers will be shown in the output from
``cr-http-workers``.

Running the tests
-----------------

Once the workers are running, running the tests just involves the standard ``init`` and ``exec`` commands:

.. code-block:: bash

    cd $ROOT
    cosmic-ray init config.toml session.sqlite
    cosmic-ray exec config.toml session.sqlite

Remember that you'll need to run this in another terminal.

Once the tests complete you can kill the ``cr-http-workers`` process. There's not much more to it than that!

Limitations
-----------

The main limitation of ``cr-http-workers`` is that it can only start workers on your local machine. If you want to run
workers on other machines, you'll need to use some other mechanism. But very often, being able to run multiple workers
on a single machine is a huge gain for mutation testing. Mutation testing time will scale down linearly with the number
of workers you run, so running 4 workers on your system will - within certain limits - let you run your mutation testing
4 times faster.

Alternatives to HttpDistributor
===============================

If ``HttpDistributor`` doesn't meet your needs, Cosmic Ray allows you to write your own distributor and use it as a
plugin. You might want to write a distributor plugin using `Celery
<https://docs.celeryproject.org/en/stable/getting-started/introduction.html>`_, for example, to take advantage of its
sophisticated message bus.