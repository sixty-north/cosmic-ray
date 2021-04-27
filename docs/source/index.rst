.. Cosmic Ray documentation documentation master file, created by
   sphinx-quickstart on Fri Oct 27 12:29:41 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Cosmic Ray: mutation testing for Python
=======================================

*"Four human beings -- changed by space-born cosmic rays into something more than merely human."*
*— The Fantastic Four*

Cosmic Ray is a mutation testing tool for Python 3. It makes small changes to
your source code, running your test suite for each one. If a test suite passes
on mutated code, then you have a mismatch between your tests and your
functionality.

Cosmic Ray has been successfully used on a wide variety of projects ranging from
assemblers to oil exploration software.

**This documentation is a bit out of date, but we're working to get it in good order!**


.. toctree::
   :maxdepth: 1
   :caption: Contents

   installation
   quickstart
   theory
   concepts
   commands
   operators
   filters
   distributed
   implementation
   tests
   continuous_integration
   badge


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
