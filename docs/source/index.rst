.. Cosmic Ray documentation documentation master file, created by
   sphinx-quickstart on Fri Oct 27 12:29:41 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Cosmic Ray: mutation testing for Python
=======================================

   "Four human beings -- changed by space-born cosmic rays into something more than merely human."

   -- The Fantastic Four

Cosmic Ray is a mutation testing tool for Python 3. It makes small changes to your production source code, running your
test suite for each change. If a test suite passes on mutated code, then you have a mismatch between your tests and your
functionality. 

Like coverage analysis, mutation testing helps ensure that you're testing all of your code. But while coverage only
tells you if a line of code is executed, mutation testing will determine if your tests actually check the behavior of your
code. This adds tremendous value to your test suite by helping it fulfill its primary role: making sure your code
does what you expect it to do!

Cosmic Ray has been successfully used on a wide variety of projects ranging from
assemblers to oil exploration software.

Contents
========

.. toctree::
   :maxdepth: 1

   theory
   tutorials/intro/index
   tutorials/distributed/index
   concepts
   how-tos/index
   reference/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
