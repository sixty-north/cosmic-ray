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
3. The publish job builds distributions and uploads them to PyPI.

Releasing a new version
=======================

Releases now use ``uv version`` instead of ``bump-my-version``.

Option 1: Use the helper script
-------------------------------

From a clean working tree on the branch you want to release:

.. code-block:: bash

   tools/release.py patch

This script:

1. Verifies preconditions (git repository, clean tree, existing remote).
2. Bumps the version in ``pyproject.toml`` using ``uv version --bump``.
3. Creates a commit.
4. Creates an annotated tag named ``release/vX.Y.Z``.
5. Pushes the branch and tag to the configured remote.

Use ``tools/release.py --help`` for options such as ``--dry-run``,
``--branch``, ``--push-ref``, and ``--remote``.

Option 2: Run commands manually
-------------------------------

.. code-block:: bash

   uv version --bump patch
   VERSION="$(uv version --short)"
   git add pyproject.toml
   git commit -m "Release v${VERSION}"
   git tag -a "release/v${VERSION}" -m "Release v${VERSION}"
   git push origin "HEAD:$(git branch --show-current)"
   git push origin "release/v${VERSION}"

Releasing from historical commits
---------------------------------

GitHub manual workflow dispatch runs on branch or tag refs, not arbitrary commit
SHAs. To release from a historical point, create a branch at that commit first,
then run the normal release process from that branch.
