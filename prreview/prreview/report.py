"""Output for pull request reviews: Markdown (for comments), text and JSON."""

from __future__ import annotations

import json

from .rules import Finding


def _summary_sentence(summary: dict) -> str:
    folders = ", ".join(f"{name} ({count})" for name, count in list(summary["by_folder"].items())[:4])
    return (f"Changes {summary['files']} file(s): +{summary['added']} / -{summary['removed']} lines"
            f"{', mainly in ' + folders if folders else ''}.")


def render_markdown(summary: dict, findings: list[Finding], ai_summary: str | None = None) -> str:
    out = ["## Pull request review", "", _summary_sentence(summary), ""]
    if ai_summary:
        out += ["### What this change does", "", ai_summary.strip(), ""]
    if not findings:
        out.append("No automatic review findings. A human review is still needed.")
        return "\n".join(out) + "\n"
    out += ["### Findings", "", "| Severity | Issue | Where | Why it matters |", "|---|---|---|---|"]
    for f in findings:
        where = f"`{f.file}:{f.line}`" if f.line else f"`{f.file}`"
        out.append(f"| {f.severity} | {f.title} | {where} | {f.detail} |")
    counts = {s: sum(1 for f in findings if f.severity == s) for s in ("High", "Medium", "Low")}
    out += ["", f"Totals: High {counts['High']}, Medium {counts['Medium']}, Low {counts['Low']}."]
    return "\n".join(out) + "\n"


def render_text(summary: dict, findings: list[Finding], ai_summary: str | None = None) -> str:
    out = [_summary_sentence(summary)]
    if ai_summary:
        out += ["", ai_summary.strip()]
    if not findings:
        out += ["", "No automatic review findings."]
        return "\n".join(out)
    out.append("")
    for f in findings:
        where = f"{f.file}:{f.line}" if f.line else f.file
        out.append(f"[{f.severity}] {f.title} ({where})")
        out.append(f"    {f.detail}")
    return "\n".join(out)


def render_json(summary: dict, findings: list[Finding], ai_summary: str | None = None) -> str:
    return json.dumps({"summary": summary, "ai_summary": ai_summary,
                       "findings": [f.to_dict() for f in findings]}, indent=2)
