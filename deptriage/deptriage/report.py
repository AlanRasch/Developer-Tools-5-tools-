"""Text, Markdown and JSON output for dependency findings."""

from __future__ import annotations

import json

from .triage import Finding


def _fix_hint(f: Finding) -> str:
    return f"upgrade to {f.fixed_in} or newer" if f.fixed_in else "no fixed version published yet"


def render_text(findings: list[Finding], errors: list[str], scanned: int, unpinned: list[str]) -> str:
    out = [f"Scanned {scanned} pinned package(s).",
           f"Findings: {len(findings)}  (High: {sum(f.priority == 'High' for f in findings)}, "
           f"Medium: {sum(f.priority == 'Medium' for f in findings)}, "
           f"Low: {sum(f.priority == 'Low' for f in findings)})"]
    if unpinned:
        out.append(f"Not pinned, so not checked: {', '.join(unpinned)}. Pin them with name==version.")
    for error in errors:
        out.append(f"Could not check {error}")
    if not findings:
        out.append("\nNo known vulnerabilities found in the pinned packages.")
        return "\n".join(out)
    out.append("")
    for f in findings:
        used = "imported by this project" if f.imported else "not imported by this project"
        out.append(f"[{f.priority}] {f.package}=={f.version}  {f.vuln_id}  ({f.severity}, {used})")
        if f.summary:
            out.append(f"    {f.summary}")
        out.append(f"    Fix: {_fix_hint(f)}")
    return "\n".join(out)


def render_markdown(findings: list[Finding], errors: list[str], scanned: int, unpinned: list[str]) -> str:
    out = ["# Dependency Security Triage", "",
           f"Scanned **{scanned}** pinned package(s). Findings: **{len(findings)}**.", ""]
    if unpinned:
        out.append(f"Not pinned, so not checked: {', '.join(f'`{u}`' for u in unpinned)}.\n")
    if not findings:
        out.append("No known vulnerabilities found in the pinned packages.")
    else:
        out.append("| Priority | Package | Vulnerability | Severity | Used by project | Fix |")
        out.append("|---|---|---|---|---|---|")
        for f in findings:
            out.append(f"| {f.priority} | `{f.package}=={f.version}` | {f.vuln_id} | {f.severity} | "
                       f"{'yes' if f.imported else 'no'} | {_fix_hint(f)} |")
    for error in errors:
        out.append(f"\n- Could not check {error}")
    return "\n".join(out) + "\n"


def render_json(findings: list[Finding], errors: list[str], scanned: int, unpinned: list[str]) -> str:
    return json.dumps({
        "scanned": scanned,
        "unpinned": unpinned,
        "errors": errors,
        "findings": [f.to_dict() for f in findings],
    }, indent=2)
