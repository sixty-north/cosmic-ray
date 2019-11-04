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

You'll often want to install Cosmic Ray into its own virtual environment. In
earlier versions we suggested installing Cosmic Ray into the same environment as
the project being tested, but that's no longer the case. In recent versions,
Cosmic Ray will create temporary virtual environments for the code under test,
so the environments for Cosmic Ray and the code under test are safely separated.
