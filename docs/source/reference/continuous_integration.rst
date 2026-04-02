========================
 Continuous Integration
========================

Cosmic Ray uses GitHub Actions for continuous integration and release
automation.

On every push and pull request, the ``Python package`` workflow runs linting and
tests across supported Python versions.

Release publishing is tag-driven:

1. Create and push a tag with the ``release/`` prefix (for example
   ``release/v8.5.0``).
2. GitHub Actions detects the tag and runs the publish job.
3. The publish job builds distributions and uploads them to PyPI. Version
   metadata comes from the Git tag through ``hatch-vcs``.

Releasing a new version
=======================

Releases use dynamic VCS-based versioning. ``pyproject.toml`` does not contain
a static ``project.version`` value.

Option 1: Use the helper script
-------------------------------

From a clean working tree on the commit you want to release:

.. code-block:: bash

   tools/release.py patch

This script:

1. Verifies preconditions (git repository, clean tree, existing remote).
2. Finds the latest ``release/vX.Y.Z`` tag.
3. Computes the next semantic version from the requested bump component.
4. Creates an annotated tag named ``release/vX.Y.Z`` at the selected ref.
5. Pushes the tag to the configured remote.

Use ``tools/release.py --help`` for options such as ``--dry-run``,
``--from-ref``, ``--next-version-only``, ``--no-push``, and ``--remote``.

Option 2: Run commands manually
-------------------------------

.. code-block:: bash

   VERSION=8.5.0
   git tag -a "release/v${VERSION}" -m "Release v${VERSION}"
   git push origin "release/v${VERSION}"

Version metadata for sdist/wheel is then derived from the release tag during
the build.

Development versions
--------------------

Outside a release tag, development builds use VCS-derived versions from
``hatch-vcs``/``setuptools-scm`` (for example ``8.5.1.dev3+g<hash>``), making
it obvious the build is not a final release.

Releasing from historical commits
---------------------------------

GitHub manual workflow dispatch runs on branch or tag refs, not arbitrary commit
SHAs. To release from a historical point, create a branch at that commit first,
then run the normal release process from that branch.
