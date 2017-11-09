========================
 Continuous Integration
========================

Cosmic Ray has a continuous integration system based on `Travis
<https://travis-ci.org>`__. Whenever we push new changes to our github
repository, travis runs a set of tests. These :doc:`tests <tests>` include
low-level unit tests, end-to-end integration tests, static analysis (e.g.
linting), and testing documentation builds. Generally speaking, these tests are
run on all versions of Python which we support.

Automated release deployment
============================

Cosmic Ray also has an automated release deployment scheme. Whenever you push
changes to `the release
branch <https://github.com/sixty-north/cosmic-ray/tree/release>`__, travis attempts
to make a new release. This process involves determining the release version by
reading ``cosmic_ray/version.py``, creating and uploading PyPI distributions, and
creating new release tags in git.

Releasing a new version
-----------------------

As described above, the release process for Cosmic Ray is largely automatic. In
order to do a new release, you simply need to:

1. Bump the version in ``cosmic_ray.version``. This can be a major, minor, or
   patch bump, but the change needs to be *up*.
2. Commit the version bump to ``master`` and push it to ``master`` on github.
3. Push the changes to the ``release`` branch on github.

Once the push is made to ``release``, the automated release system will take over.

Note that only the Python 3.6 travis build will attempt to make a release
deployment. So to see the progress of your release, check the output for that
build.
