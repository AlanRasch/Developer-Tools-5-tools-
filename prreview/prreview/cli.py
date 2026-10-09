"""Command-line interface:  prreview review [options]"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .diffparse import parse_diff
from .gitops import git_diff
from .report import render_json, render_markdown, render_text
from .rules import review, summarize

THRESHOLDS = {"high": 0, "medium": 1, "low": 2}
MAX_AI_INPUT = 12000


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="prreview", description="Review a pull request's changes for common risks.")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("review", help="review the changes between a base branch and HEAD")
    src = r.add_mutually_exclusive_group()
    src.add_argument("--base", default="main", help="branch the change is compared with (default: main)")
    src.add_argument("--diff-file", help="read a saved diff instead of running git")
    r.add_argument("--head", default="HEAD", help="branch or commit to review (default: HEAD)")
    r.add_argument("--repo", default=".", help="git repository folder (default: current folder)")
    r.add_argument("--format", choices=["markdown", "text", "json"], default="markdown")
    r.add_argument("-o", "--output", help="write the review to a file (for example, to post as a comment)")
    r.add_argument("--fail-on", choices=["high", "medium", "low", "none"], default="none",
                   help="exit with code 1 when findings at this severity or higher exist")
    r.add_argument("--with-claude", action="store_true",
                   help="add a plain-language summary written by Claude (needs ANTHROPIC_API_KEY)")
    return p


def ai_summary(diff_text: str) -> str:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("--with-claude needs ANTHROPIC_API_KEY in your environment")
    import anthropic
    client = anthropic.Anthropic(api_key=key)
    prompt = ("Summarise this pull request for a reviewer in 3 short bullet points: what changed, "
              "why it probably matters, and what the reviewer should check. Plain language.\n\n"
              + diff_text[:MAX_AI_INPUT])
    response = client.messages.create(model=os.getenv("PR_MODEL", "claude-sonnet-5-5"), max_tokens=500,
                                      messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in response.content if getattr(b, "type", "") == "text")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.diff_file:
            diff_text = Path(args.diff_file).read_text(encoding="utf-8")
        else:
            diff_text = git_diff(args.base, args.head, Path(args.repo).resolve())
        changes = parse_diff(diff_text)
        if not changes:
            print("No changes found between the two branches.")
            return 0
        findings = review(changes)
        summary = summarize(changes)
        narrative = ai_summary(diff_text) if args.with_claude else None
    except (OSError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    render = {"markdown": render_markdown, "text": render_text, "json": render_json}[args.format]
    text = render(summary, findings, narrative)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)

    if args.fail_on != "none":
        limit = THRESHOLDS[args.fail_on]
        order = {"High": 0, "Medium": 1, "Low": 2}
        if any(order[f.severity] <= limit for f in findings):
            return 1
    return 0
