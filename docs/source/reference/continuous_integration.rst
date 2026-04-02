========================
 Continuous Integration
========================

Cosmic Ray uses GitHub Actions for continuous integration and release
automation.

On every push and pull request, the ``Run tests`` workflow runs linting and
tests across supported Python versions.

Release publishing is managed by the manually triggered ``release`` workflow:

1. Select a ref (branch/tag/SHA) and bump component (major/minor/patch).
2. The workflow computes the next ``release/vX.Y.Z`` tag.
3. It runs lint/tests across supported Python versions at the selected commit.
4. If tests pass, it creates/pushes the tag, builds distributions, and uploads
   them to PyPI.
5. Version metadata comes from the release tag through ``hatch-vcs``.

Releasing a new version
=======================

Releases use dynamic VCS-based versioning. ``pyproject.toml`` does not contain a
static ``project.version`` value.

Option 1: Use GitHub Actions (recommended)
------------------------------------------

From the GitHub UI, run the ``release`` workflow manually:

1. Open the ``release`` workflow.
2. Choose ``part`` (``patch``, ``minor``, or ``major``).
3. Choose ``ref`` (defaults to ``master``).
4. Start the workflow.

The workflow requires a repository secret named ``RELEASE_TOKEN`` (a PAT with
repository write plus workflow permissions) so it can push release tags even
when the target commit updates workflow files.

The workflow computes the next release tag automatically and publishes only
after test/lint jobs succeed.

Option 2: Use the helper script (local/manual fallback)
-------------------------------------------------------

From a clean working tree on the commit you want to release:

.. code-block:: bash

   tools/release.py patch

Use ``tools/release.py --help`` for options such as ``--dry-run``,
``--from-ref``, ``--next-version-only``, ``--no-push``, and ``--remote``.

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
