"""Command-line interface:
  commitcraft message    write a commit message for staged changes
  commitcraft changelog  build a changelog section from commits since the last tag
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .changelog import prepend_to_changelog, render_section
from .diffstat import parse_diff
from .gitops import latest_tag, staged_diff, subjects_since
from .message import build_message, check_message


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="commitcraft", description="Write commit messages and changelogs for you.")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("message", help="write a commit message for the staged changes")
    m.add_argument("--repo", default=".", help="git repository folder (default: current folder)")
    m.add_argument("--diff-file", help="read a saved diff instead of the staged changes")
    m.add_argument("-o", "--output", help="save the message to a file (use with: git commit -F FILE)")

    c = sub.add_parser("changelog", help="build a changelog section from commits")
    c.add_argument("--repo", default=".", help="git repository folder (default: current folder)")
    c.add_argument("--version", required=True, help="version for the new section, for example 1.2.0")
    c.add_argument("--since", help="tag to start from (default: the latest tag)")
    c.add_argument("--write", action="store_true", help="add the section to CHANGELOG.md (default: print only)")
    c.add_argument("--file", default="CHANGELOG.md")
    return p


def cmd_message(args) -> int:
    if args.diff_file:
        diff_text = Path(args.diff_file).read_text(encoding="utf-8")
    else:
        diff_text = staged_diff(Path(args.repo).resolve())
    message = build_message(parse_diff(diff_text))
    for problem in check_message(message):
        print(f"Note: {problem}", file=sys.stderr)
    if args.output:
        Path(args.output).write_text(message, encoding="utf-8")
        print(f"Wrote {args.output}. Commit with: git commit -F {args.output}")
    else:
        print(message)
    return 0


def cmd_changelog(args) -> int:
    repo = Path(args.repo).resolve()
    tag = args.since or latest_tag(repo)
    subjects = subjects_since(tag, repo)
    section = render_section(args.version, subjects)
    if not args.write:
        print(f"Commits since {tag or 'the first commit'}: {len(subjects)}\n")
        print(section)
        return 0
    target = Path(args.file) if Path(args.file).is_absolute() else repo / args.file
    result = prepend_to_changelog(target, section)
    print(f"{result.capitalize()} {target}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return cmd_message(args) if args.cmd == "message" else cmd_changelog(args)
    except (OSError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2
