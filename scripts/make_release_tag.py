"""Create a git tag for the current version.

This reads the version file, finds the current version therein, creates a git
tag, and pushes that tag to `origin`.
"""

import cosmic_ray_tooling as tooling

if __name__ == '__main__':
    version, version_info = tooling.read_version(tooling.VERSION_FILE)
    tooling.create_tag_and_push(version)
