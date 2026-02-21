#!/usr/bin/env python3
"""Bump, tag, and push a Cosmic Ray release."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", choices=("major", "minor", "patch"), help="Version component to bump.")
    parser.add_argument("--remote", default="origin", help="Remote name to push to.")
    parser.add_argument(
        "--push-ref",
        help="Remote branch ref to push HEAD to (required if HEAD is detached).",
    )
    parser.add_argument(
        "--branch",
        help="Expected current branch. If provided and different from HEAD, the release is aborted.",
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
        help="Print actions and validations without changing files, creating tags, or pushing.",
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


def current_branch() -> str:
    return run("git", "branch", "--show-current", capture_output=True)


def ensure_remote_exists(remote: str) -> None:
    remotes = run("git", "remote", capture_output=True).splitlines()
    if remote not in remotes:
        fail(f"remote {remote!r} does not exist")


def ensure_no_existing_tag(tag: str) -> None:
    local = subprocess.run(["git", "show-ref", "--verify", f"refs/tags/{tag}"], check=False, capture_output=True)
    if local.returncode == 0:
        fail(f"tag {tag!r} already exists locally")


def ensure_no_existing_remote_tag(remote: str, tag: str) -> None:
    remote_result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--tags", remote, f"refs/tags/{tag}"],
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
    args = parse_args()

    ensure_tool("git")
    ensure_tool("uv")
    ensure_git_repo()
    ensure_remote_exists(args.remote)

    branch = current_branch()
    if args.branch and branch != args.branch:
        fail(f"current branch is {branch!r}, expected {args.branch!r}")

    push_ref = args.push_ref or branch
    if not push_ref:
        fail("detached HEAD detected; pass --push-ref to specify which remote branch to update")

    if not args.allow_dirty:
        ensure_clean_worktree()

    current = run("uv", "version", "--short", capture_output=True)
    new = run("uv", "version", "--bump", args.part, "--dry-run", "--short", capture_output=True)
    tag = f"release/v{new}"

    ensure_no_existing_tag(tag)
    ensure_no_existing_remote_tag(args.remote, tag)

    print(
        f"Prepared release:\n"
        f"  branch: {branch or '(detached HEAD)'}\n"
        f"  push ref: {push_ref}\n"
        f"  remote: {args.remote}\n"
        f"  current version: {current}\n"
        f"  new version: {new}\n"
        f"  tag: {tag}"
    )

    if args.dry_run:
        print("Dry-run mode: no changes were made.")
        return

    if not args.yes and not confirm("Continue with release?"):
        fail("release aborted by user", code=2)

    run("uv", "version", "--bump", args.part, mutates=True)
    run("git", "add", "pyproject.toml", mutates=True)
    run("git", "commit", "-m", f"Release v{new}", mutates=True)
    run("git", "tag", "-a", tag, "-m", f"Release v{new}", mutates=True)
    run("git", "push", args.remote, f"HEAD:{push_ref}", mutates=True)
    run("git", "push", args.remote, tag, mutates=True)

    print("Release push complete. Tag-triggered publish workflow should start on GitHub Actions.")


if __name__ == "__main__":
    main()
