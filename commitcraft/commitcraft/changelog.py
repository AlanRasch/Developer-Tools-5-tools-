"""Build a changelog section from commit messages, grouped by kind of change."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

CONVENTIONAL = re.compile(r"^(?P<type>\w+)(\((?P<scope>[^)]+)\))?(?P<breaking>!)?: (?P<text>.+)$")
SECTIONS = [
    ("Breaking changes", None),
    ("Added", "feat"),
    ("Fixed", "fix"),
    ("Changed", "refactor"),
    ("Performance", "perf"),
    ("Documentation", "docs"),
    ("Other", None),
]


def parse_subject(subject: str) -> dict:
    match = CONVENTIONAL.match(subject.strip())
    if not match:
        return {"type": "other", "scope": None, "breaking": False, "text": subject.strip()}
    return {"type": match.group("type").lower(), "scope": match.group("scope"),
            "breaking": bool(match.group("breaking")), "text": match.group("text")}


def render_section(version: str, subjects: list[str], on: date | None = None) -> str:
    parsed = [parse_subject(s) for s in subjects if s.strip()]
    out = [f"## [{version}] - {(on or date.today()).isoformat()}", ""]
    used = False
    for title, kind in SECTIONS:
        if title == "Breaking changes":
            items = [p for p in parsed if p["breaking"]]
        elif title == "Other":
            known = {k for _, k in SECTIONS if k}
            items = [p for p in parsed if not p["breaking"] and p["type"] not in known]
        else:
            items = [p for p in parsed if not p["breaking"] and p["type"] == kind]
        if not items:
            continue
        used = True
        out.append(f"### {title}")
        for p in items:
            scope = f"**{p['scope']}:** " if p["scope"] else ""
            out.append(f"- {scope}{p['text']}")
        out.append("")
    if not used:
        out.append("- No notable changes.\n")
    return "\n".join(out).rstrip() + "\n"


def prepend_to_changelog(path: Path, section: str) -> str:
    """Insert the new section below the '# Changelog' heading (or create the file)."""
    if not path.exists():
        path.write_text("# Changelog\n\n" + section, encoding="utf-8")
        return "created"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_at = i + 1
            break
    head = "".join(lines[:insert_at])
    rest = "".join(lines[insert_at:]).lstrip("\n")
    path.write_text(f"{head}\n{section}\n{rest}", encoding="utf-8")
    return "updated"
