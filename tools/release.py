#!/usr/bin/env python3
"""Compute, tag, and optionally push a Cosmic Ray release."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass

RELEASE_TAG_RE = re.compile(r"^release/v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
RUN_VERBOSE = True


@dataclass(frozen=True, order=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> SemVer:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value)
        if match is None:
            fail(f"invalid semantic version: {value!r} (expected MAJOR.MINOR.PATCH)")
        return cls(*(int(group) for group in match.groups()))

    @classmethod
    def from_release_tag(cls, value: str) -> SemVer | None:
        match = RELEASE_TAG_RE.fullmatch(value)
        if match is None:
            return None
        return cls(
            int(match.group("major")),
            int(match.group("minor")),
            int(match.group("patch")),
        )

    def bump(self, part: str) -> SemVer:
        if part == "major":
            return SemVer(self.major + 1, 0, 0)
        if part == "minor":
            return SemVer(self.major, self.minor + 1, 0)
        if part == "patch":
            return SemVer(self.major, self.minor, self.patch + 1)
        fail(f"unknown version component: {part!r}")
        raise AssertionError("unreachable")

    def release_tag(self) -> str:
        return f"release/v{self}"

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", choices=("major", "minor", "patch"), help="Version component to bump.")
    parser.add_argument("--remote", default="origin", help="Remote name for tag checks and push.")
    parser.add_argument(
        "--from-ref",
        default="HEAD",
        help="Git ref to tag. Defaults to HEAD.",
    )
    parser.add_argument(
        "--base-version",
        default="0.0.0",
        help="Version to use when no release tags exist.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow running when the git working tree is not clean.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions and validations without creating or pushing tags.",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Create the tag locally without pushing it.",
    )
    parser.add_argument(
        "--next-version-only",
        action="store_true",
        help="Print the computed next version and exit.",
    )
    return parser.parse_args()


def fail(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(
    *args: str,
    capture_output: bool = False,
    dry_run: bool = False,
    mutates: bool = False,
) -> str:
    command = " ".join(args)
    if RUN_VERBOSE:
        print(f"+ {command}")
    if dry_run and mutates:
        return ""

    completed = subprocess.run(
        args,
        text=True,
        check=False,
        capture_output=capture_output,
    )
    if completed.returncode != 0:
        if completed.stdout:
            print(completed.stdout, file=sys.stderr, end="")
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="")
        fail(f"command failed ({completed.returncode}): {command}")

    return completed.stdout.strip() if capture_output else ""


def ensure_tool(name: str) -> None:
    if shutil.which(name) is None:
        fail(f"required tool is not available on PATH: {name}")


def ensure_git_repo() -> None:
    inside = run("git", "rev-parse", "--is-inside-work-tree", capture_output=True)
    if inside != "true":
        fail("current directory is not inside a git repository")


def ensure_clean_worktree() -> None:
    status = run("git", "status", "--porcelain", capture_output=True)
    if status:
        fail("git working tree is not clean")


def remote_exists(remote: str) -> bool:
    remotes = run("git", "remote", capture_output=True).splitlines()
    return remote in remotes


def parse_remote_tag_line(line: str) -> str | None:
    # git ls-remote --tags --refs output is "<sha>\trefs/tags/<tag-name>"
    parts = line.split("\t", 1)
    if len(parts) != 2:
        return None
    ref = parts[1]
    if not ref.startswith("refs/tags/"):
        return None
    return ref.removeprefix("refs/tags/")


def all_release_versions(remote: str | None) -> list[SemVer]:
    tags = run("git", "tag", "--list", "release/v*", capture_output=True).splitlines()
    versions = [v for v in (SemVer.from_release_tag(tag) for tag in tags) if v is not None]

    if remote is not None:
        remote_lines = run(
            "git",
            "ls-remote",
            "--tags",
            "--refs",
            remote,
            "refs/tags/release/v*",
            capture_output=True,
        ).splitlines()
        remote_tags = [tag for tag in (parse_remote_tag_line(line) for line in remote_lines) if tag is not None]
        versions.extend(v for v in (SemVer.from_release_tag(tag) for tag in remote_tags) if v is not None)

    return versions


def ensure_no_existing_tag(tag: str) -> None:
    local = subprocess.run(["git", "show-ref", "--verify", f"refs/tags/{tag}"], check=False, capture_output=True)
    if local.returncode == 0:
        fail(f"tag {tag!r} already exists locally")


def ensure_no_existing_remote_tag(remote: str, tag: str) -> None:
    remote_result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--tags", "--refs", remote, f"refs/tags/{tag}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if remote_result.returncode == 0:
        fail(f"tag {tag!r} already exists on remote {remote!r}")
    if remote_result.returncode not in (2,):
        if remote_result.stdout:
            print(remote_result.stdout, file=sys.stderr, end="")
        if remote_result.stderr:
            print(remote_result.stderr, file=sys.stderr, end="")
        fail(f"unable to verify tag existence on remote {remote!r}")


def confirm(prompt: str) -> bool:
    response = input(f"{prompt} [y/N]: ").strip().lower()
    return response in {"y", "yes"}


def main() -> None:
    global RUN_VERBOSE
    args = parse_args()
    RUN_VERBOSE = not args.next_version_only

    ensure_tool("git")
    ensure_git_repo()

    has_remote = remote_exists(args.remote)
    if not has_remote and not args.no_push:
        fail(f"remote {args.remote!r} does not exist")

    if not args.allow_dirty:
        ensure_clean_worktree()

    base_version = SemVer.parse(args.base_version)
    latest = max(all_release_versions(args.remote if has_remote else None), default=base_version)
    new = latest.bump(args.part)
    tag = new.release_tag()

    ensure_no_existing_tag(tag)
    if has_remote:
        ensure_no_existing_remote_tag(args.remote, tag)

    if args.next_version_only:
        print(new)
        return

    print(
        f"Prepared release:\n"
        f"  from ref: {args.from_ref}\n"
        f"  remote: {args.remote}\n"
        f"  push tag: {not args.no_push}\n"
        f"  latest version: {latest}\n"
        f"  new version: {new}\n"
        f"  tag: {tag}"
    )

    if args.dry_run:
        print("Dry-run mode: no changes were made.")
        return

    if not args.yes and not confirm("Continue with release tag creation?"):
        fail("release aborted by user", code=2)

    run("git", "tag", "-a", tag, args.from_ref, "-m", f"Release v{new}", mutates=True)
    if not args.no_push:
        run("git", "push", args.remote, tag, mutates=True)

    print("Release tag creation complete.")
    if args.no_push:
        print(f"To push later: git push {args.remote} {tag}")


if __name__ == "__main__":
    main()
