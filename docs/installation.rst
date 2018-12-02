==============
 Installation
==============

``pip``
=======

The simplest way to install Cosmic Ray is with ``pip``:

::

    pip install cosmic_ray

This will install the most recent uploaded version in PyPI.

From source
===========

If you want to install Cosmic Ray from source you need to use
``setup.py``:

::

    python setup.py install

Virtual environments
--------------------

You'll often want to install Cosmic Ray into a virtual environment.
However, you generally *don't* want to install it into its own. Rather,
you want to install it into the virtual environment of the project you
want to test. This ensures that the test runners have access to the
modules they are supposed to test.