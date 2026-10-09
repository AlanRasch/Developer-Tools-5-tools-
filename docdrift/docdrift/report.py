"""Text, Markdown and JSON output for documentation issues."""

from __future__ import annotations

import json

from .checks import Issue


def render_text(issues: list[Issue], docs_checked: int) -> str:
    out = [f"Checked {docs_checked} document(s)."]
    if not issues:
        out.append("No drift found: the documentation matches the code.")
        return "\n".join(out)
    out.append(f"Found {len(issues)} issue(s):\n")
    for i in issues:
        out.append(f"{i.file}:{i.line}  [{i.kind}]  {i.message}")
    return "\n".join(out)


def render_markdown(issues: list[Issue], docs_checked: int) -> str:
    out = ["# Documentation Drift Report", "", f"Checked **{docs_checked}** document(s).", ""]
    if not issues:
        out.append("No drift found: the documentation matches the code.")
        return "\n".join(out) + "\n"
    out += ["| Document | Line | Type | Problem |", "|---|---:|---|---|"]
    for i in issues:
        out.append(f"| `{i.file}` | {i.line} | {i.kind} | {i.message} |")
    return "\n".join(out) + "\n"


def render_json(issues: list[Issue], docs_checked: int) -> str:
    return json.dumps({"documents_checked": docs_checked, "issues": [i.to_dict() for i in issues]}, indent=2)
