"""Command-line interface:  envdoctor [folder] [--json]"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .doctor import run_checks, summarize


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="envdoctor",
                                description="Check that this computer is ready to work on a project.")
    p.add_argument("folder", nargs="?", default=".", help="project folder (default: current folder)")
    p.add_argument("--json", action="store_true", help="print the results as JSON")
    return p


def render(results, counts) -> str:
    lines = []
    for r in results:
        lines.append(f"[{r.status}] {r.name}: {r.message}")
        if r.status != "PASS" and r.fix:
            lines.append(f"       Fix: {r.fix}")
    lines.append("")
    lines.append(f"Summary: {counts['PASS']} passed, {counts['WARN']} warning(s), {counts['FAIL']} failure(s).")
    if counts["FAIL"]:
        lines.append("Fix the failures above, then run envdoctor again.")
    elif counts["WARN"]:
        lines.append("Everything required is in place. Look at the warnings when you have a moment.")
    else:
        lines.append("This computer is ready for the project.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.folder).resolve()
    if not root.is_dir():
        print(f"Error: folder not found: {root}", file=sys.stderr)
        return 2
    results = run_checks(root)
    counts = summarize(results)
    if args.json:
        print(json.dumps({"results": [r.to_dict() for r in results], "summary": counts}, indent=2))
    else:
        print(render(results, counts))
    return 1 if counts["FAIL"] else 0
