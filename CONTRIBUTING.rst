=================
How to contribute
=================

Third-party patches are welcomed for improving Cosmic Ray. There is plenty of work to be done on bug fixes,
documentation, new features, and improved tooling.

Although we want to keep it as easy as possible to contribute changes that
get things working in your environment, there are a few guidelines that we
need contributors to follow so that we can have a chance of keeping on
top of things.


Getting Started
===============

The easiest way to help is by submitting issues reporting defects or
requesting additional features.

* Make sure you have a `GitHub account <https://github.com/signup/free>`_

* Submit an issue, assuming one does not already exist.

  * Clearly describe the issue including steps to reproduce when it is a bug.

  * If appropriate, include a Cosmic Ray config file and, if possible, some way for us to get access to
    the code you're working with.
  
  * Make sure you mention the earliest version that you know has the issue.
  
* Fork the repository on GitHub


Making Changes
==============

* You must own the copyright to the patch you're submitting, and be in a
  position to transfer the copyright to Sixty North by agreeing to the either
  the |ICLA|
  (for private individuals) or the |ECLA|
  (for corporations or other organisations).
* Make small commits in logical units.
* Ensure your code is in the spirit of `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_,
  although we accept that much of what is in PEP 8 are guidelines
  rather than rules, so we value readability over strict compliance.
* Check for unnecessary whitespace with ``git diff --check`` before committing.
* Make sure your commit messages use Conventional Commits::


    fix(git-filter): handle binary files

    Git filtering failed when a repository contained non-text files.
    Skip binary files so filtering behaves consistently.

    Refs: #582

  The first line should use ``<type>(<optional-scope>): <subject>`` where
  ``type`` is typically one of ``feat``, ``fix``, ``refactor``, ``perf``,
  ``docs``, ``test``, or ``chore``.
* For breaking changes, use either ``!`` in the type/scope (for example
  ``feat(api)!: ...``) or include a ``BREAKING CHANGE: ...`` footer.


* Make sure you have added the necessary tests for your changes.
* Run **all** the tests to assure nothing else was accidentally broken.

Making Trivial Changes
======================

Documentation
-------------

For changes of a trivial nature to comments and documentation, it is not
always necessary to create a new issue. In this case, use a Conventional
Commit with type ``docs``::

    docs(contributing): clarify commit message examples

Submitting Changes
==================

* Agree to the |ICLA| or the |ECLA|
  by attaching a copy of the current CLA to an email (so we know which
  version you're agreeing to). The body of the message should contain
  the text "I, <your name>, [representing <your company>] have read the
  attached CLA and agree to its terms."  Send the email to austin@sixty-north.com
* Push your changes to a topic branch in your fork of the repository.
* Submit a pull request to the repository in the sixty-north organization.


Additional Resources
====================

* |ICLA|
* |ECLA|
* `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_
* `General GitHub documentation <http://help.github.com/>`_
* `GitHub pull request documentation <http://help.github.com/send-pull-requests/>`_

.. |ICLA| replace:: `Individual Contributors License Agreement <https://github.com/sixty-north/cosmic-ray/raw/master/docs/source/legal/cosmic-ray-individual-cla.pdf>`__
.. |ECLA| replace:: `Entity Contributor License Agreement <https://github.com/sixty-north/cosmic-ray/raw/master/docs/source/legal/cosmic-ray-entity-cla.pdf>`__
