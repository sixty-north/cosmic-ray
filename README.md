[![Build Status](https://travis-ci.org/sixty-north/cosmic-ray.png?branch=master)](https://travis-ci.org/sixty-north/cosmic-ray) [![Code Health](https://landscape.io/github/sixty-north/cosmic-ray/master/landscape.svg?style=flat)](https://landscape.io/github/sixty-north/cosmic-ray/master) [![Documentation](https://readthedocs.org/projects/cosmic-ray/badge/?version=latest)](http://cosmic-ray.readthedocs.org/en/latest/)

# Cosmic Ray: mutation testing for Python

*"Four human beings -- changed by space-born cosmic rays into something more than merely human."*
*— The Fantastic Four*

Cosmic Ray is a mutation testing tool for Python.

## N.B.! Cosmic Ray is still learning how to walk!

At this time Cosmic Ray is young and incomplete. It doesn't support
all of the mutations it should, its output format is crude, it only
supports some forms of test discovery, it may fall over on exotic
modules...[the list goes on and on](https://github.com/sixty-north/cosmic-ray/issues). Still,
for the adventurous it *does* work. Hopefully things will improve
fairly rapidly.

And, of course, patches and ideas are welcome.

## The short version

If you just want to get down to the business of finding and killing
mutants, you still need to set a few things up.

### Install Cosmic Ray

First install Cosmic Ray. You can do this with `pip`:

```
pip install cosmic_ray
```

or from source:

```
python setup.py install
```

We recommend installing it into a virtual environment. Often it makes sense to
install it into the virtual environment of the package you want to test.

### Create a session and run tests

Now you're ready to start killing mutants. Cosmic Ray uses a notion of
*sessions* to encompass a full mutation testing suite. Since mutation testing
runs can take a long time, and since you might need to stop and start them,
sessions store data about the progress of a run. The first step in a full
testing run, then, is to initialize a session:

```
cosmic-ray init --baseline=10 <session name> <top module name> -- <test directory>
```

This will create a database file called `<session name>.json`. Once this is
created, you can start executing tests with the `exec` command:

```
cosmic-ray exec <session name>
```

Unless there are errors, this won't print anything.

### View the results

Once the execution is complete (i.e., all mutations have been performed and
tested), you can see the results of your session with the `report` command:

```
cosmic-ray report <session name>
```

This will print out a bunch of information about the work that was performed,
including what kinds of mutants were created, which were killed, and
– chillingly – which survived.

## Distributed testing with Celery

By default Cosmic Ray does all of its testing locally and serially, running only
one test suite at a time. This can be too slow for many real-world testing
scenarios. To help speed things up, Cosmic Ray supports distributed mutation
testing using [Celery](http://www.celeryproject.org/) to send work to more than
one machine. This is more complex to set up, but it makes mutation testing
practical for a wider range of projects.

To run Cosmic Ray in distributed mode, you first need to
install [RabbitMQ](https://www.rabbitmq.com/). Cosmic Ray uses this message
queue (via Celery) to distribute testing tasks. Once installed, start the
RabbitMQ server. This is very platform-specific, so see the instructions for
RabbitMQ on how to do this.

Once RabbitMQ is running, you need to start one or more Cosmic Ray worker tasks
to listen for commmands on the queue. Start a worker like this:

```
celery -A cosmic_ray.tasks.worker worker
```

You can start as many workers as you want. Be aware that these workers - and the
processes they spawn - need to be able to import the modules you want to test.
As a result, you generally want to start them in the virtual environment into
which you've installed Cosmic Ray.

Also remember that the workers need to be able to find and execute the tests as
expressed to the `init` command. In other words, if you used `cosmic-ray init .
. . -- tests` to initialize a session, the test loader (whether local or
distributed) will look for tests in the `test` directory. So you need to make
sure that the worker processes are running in directory where this makes sense.

Finally, once the worker(s) are running you need to use the `--dist` flag when
you run `cosmic-ray exec`:
```
cosmic-ray exec --dist
```

Note that all of the other Cosmic Ray commands --- `init`, `report`, etc. ---
don't need the `--dist` flag; only `exec` and `run` use it.

**[Further documentation is available at readthedocs](http://cosmic-ray.readthedocs.org/en/latest/).**
