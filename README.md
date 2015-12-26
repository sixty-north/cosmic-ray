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

Next you need to install [RabbitMQ](https://www.rabbitmq.com/). Cosmic Ray uses
this message queue (via [Celery](http://www.celeryproject.org/)) to distribute
testing tasks. Once installed, start the server. This is very platform-specific,
so see the instructions for RabbitMQ on how to do this.

Once RabbitMQ is running, you need to start one or more Cosmic Ray worker tasks
to listen for commmands on the queue. Start a worker like this:

```
celery -A cosmic_ray.worker worker
```

You can start as many workers as you want. Be aware that these workers - and the
processes they spawn - need to be able to import the modules you want to test.
As a result, you generally want to start them in the virtual environment into
which you've installed Cosmic Ray.

Finally, you're ready to start killing mutants. To do this, use Cosmic Ray's "run" command:

```
cosmic-ray run --baseline=10 <top module name> <test directory>
```

This will print out a bunch of information about what Cosmic Ray is
doing, including stuff about what kinds of mutants are being created,
which were killed, and – chillingly – which survived.

**[Further documentation is available at readthedocs](http://cosmic-ray.readthedocs.org/en/latest/).**
