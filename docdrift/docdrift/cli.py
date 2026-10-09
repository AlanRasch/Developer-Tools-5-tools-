"""Command-line interface:  docdrift check [options]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .checks import check_document, find_docs
from .code_index import build_index
from .report import render_json, render_markdown, render_text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="docdrift", description="Find documentation that no longer matches the code.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="compare the docs with the code")
    c.add_argument("--root", default=".", help="project folder (default: current folder)")
    c.add_argument("--docs", action="append",
                   help="Markdown file or folder to check, relative to --root; repeat for several "
                        "(default: README.md and docs/)")
    c.add_argument("--source", action="append",
                   help="folder with the code, relative to --root; repeat for several (default: src, or the project)")
    c.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    c.add_argument("-o", "--output", help="write the report to a file")
    c.add_argument("--fail-on-issues", action="store_true", help="exit with code 1 if any issue is found")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: project folder not found: {root}", file=sys.stderr)
        return 2

    doc_entries = [root / d for d in args.docs] if args.docs else [p for p in [root / "README.md", root / "docs"] if p.exists()]
    if args.source:
        sources = [root / s for s in args.source]
    else:
        sources = [root / "src"] if (root / "src").is_dir() else [root]
    docs = find_docs(root, doc_entries)
    if not docs:
        print("Error: no Markdown documents found to check.", file=sys.stderr)
        return 2

    index = build_index(root, sources)
    issues = []
    for doc in docs:
        issues.extend(check_document(doc, root, index))

    render = {"text": render_text, "markdown": render_markdown, "json": render_json}[args.format]
    text = render(issues, len(docs))
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    return 1 if (args.fail_on_issues and issues) else 0
