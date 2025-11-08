======================
Command Line Interface
======================

This documents each of the command line programs provided with Cosmic Ray. You can also get help on the command line by passed `--help` to any command.

``cosmic-ray``
==============

This primary program provided by Cosmic Ray is, unsurprisingly, ``cosmic-ray``. This program initializes sessions, performs mutations, and executes tests. 

.. click:: cosmic_ray.cli:cli
    :prog: cosmic-ray
    :nested: full

Concurrency
-----------

Note that most Cosmic Ray commands can be safely executed while ``exec`` is
running. One exception is ``init`` since that will rewrite the work manifest.

For example, you can run ``cr-report`` on a session while that session is being
executed. This will tell you what progress has been made.

``cr-html``
===========

.. click:: cosmic_ray.tools.html:report_html
    :prog: cr-html
    :nested: full

``cr-report``
=============

.. click:: cosmic_ray.tools.report:report
    :prog: cr-report
    :nested: full

Use ``--surviving-only`` alongside ``--show-diff`` (and/or ``--show-output``) to focus the detailed listings on
mutants whose tests survived, e.g. ``cr-report session.sqlite --show-diff --surviving-only``.

``cr-badge``
============

.. click:: cosmic_ray.tools.badge:generate_badge
    :prog: cr-badge
    :nested: full

``cr-rate``
===========

.. click:: cosmic_ray.tools.survival_rate:format_survival_rate
    :prog: cr-rate
    :nested: full

``cr-xml``
==========

.. click:: cosmic_ray.tools.xml:report_xml
    :prog: cr-xml
    :nested: full

``cr-http-workers``
=================== 

.. click:: cosmic_ray.tools.http_workers:main
    :prog: cr-http-workers
    :nested: full

``cr-filter-operators``
======================= 

**TODO**

``cr-filter-pragma``
====================

**TODO**

``cr-filter-git``
================= 

**TODO**
