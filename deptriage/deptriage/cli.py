"""Command-line interface:  dep-triage scan [options]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .osv import cached, query_osv
from .parsing import imported_modules, parse_requirements
from .report import render_json, render_markdown, render_text
from .triage import PRIORITY_RANK, scan

THRESHOLDS = {"high": 0, "medium": 1, "low": 2}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dep-triage", description="Find vulnerable dependencies and fix the urgent ones first.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="check pinned dependencies against the OSV vulnerability database")
    s.add_argument("--path", default=".", help="project folder (default: current folder)")
    s.add_argument("--requirements", default="requirements.txt", help="file with name==version lines")
    s.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    s.add_argument("-o", "--output", help="write the report to a file")
    s.add_argument("--fail-on", choices=["high", "medium", "low", "none"], default="high",
                   help="exit with code 1 if findings at this priority or higher exist (default: high)")
    s.add_argument("--cache", help="JSON file that stores results, so repeated runs do not query the network")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path).resolve()
    req = Path(args.requirements)
    req = req if req.is_absolute() else root / req
    try:
        if not req.exists():
            raise ValueError(f"requirements file not found: {req}")
        pinned, unpinned = parse_requirements(req)
        modules = imported_modules(root)
        lookup = query_osv
        if args.cache:
            lookup = cached(query_osv, args.cache)
        findings, errors = scan(pinned, lookup, modules)
    except (OSError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    render = {"text": render_text, "markdown": render_markdown, "json": render_json}[args.format]
    text = render(findings, errors, len(pinned), unpinned)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)

    if args.fail_on != "none":
        limit = THRESHOLDS[args.fail_on]
        if any(PRIORITY_RANK[f.priority] <= limit for f in findings):
            return 1
    return 0
