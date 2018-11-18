==============
 Installation
==============

``pip``
=======

The simplest way to install Cosmic Ray is with ``pip``:

::

    pip install cosmic_ray

This will install the most recent uploaded version in PyPI.

Plugins
-------

A lot of Cosmic Ray's functionality is provided by plugins, and many of these
plugins are not part of the core ``cosmic_ray`` package. Instead they are provided
by other packages (some of which are included in the same git repository as
``cosmic_ray``). Many of these can be installed with ``pip``.

=========================== =========================================
plugin                      command
=========================== =========================================
``pytest`` test runner      ``pip install cosmic_ray_pytest_runner``
``celery`` execution engine ``pip install cosmic-ray-celery3-engine``
=========================== =========================================

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

Plugins
=======

As mentioned above, much of Cosmic Ray's functionality is provided as plugins.
Besides using ``pip``, you can also install these from source. The plugin
packages which are included with the Cosmic Ray source repository can be found
in the ``plugins`` directory.

For example, the Celery3 execution engine is provided as a plugin via the
``cosmic_ray_celery3_engine`` package. You can find this package in
``plugins/execution-engines/celery3``, and you can install this plugin by running
this command in that directory:

::

    python setup.py install

Other plugin packages can be found under the ``plugins`` directory, and it's
likely that even more plugins will be available in other repositories.
