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

Changelog with git-cliff
------------------------

Changelog generation is based on ``git-cliff`` and Conventional Commits.

Configuration lives in ``cliff.toml`` and is tuned for release tags named
``release/vX.Y.Z``.

Typical usage:

.. code-block:: bash

   # Generate or refresh the full changelog from tags/commits
   git cliff --config cliff.toml -o CHANGELOG.md

   # Preview unreleased notes without writing to disk
   git cliff --config cliff.toml --unreleased

Conventional commit types such as ``feat`` and ``fix`` are grouped into changelog
sections (Added, Fixed, and so on). Non-conventional commits are filtered out.

Releasing from historical commits
---------------------------------

GitHub manual workflow dispatch runs on branch or tag refs, not arbitrary commit
SHAs. To release from a historical point, create a branch at that commit first,
then run the normal release process from that branch.
