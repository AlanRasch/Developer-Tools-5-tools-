"""Combine vulnerability data with real usage to decide what to fix first."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

from .osv import lowest_fix, severity_of
from .parsing import Dependency, is_imported

PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}


@dataclass
class Finding:
    package: str
    version: str
    vuln_id: str
    severity: str
    summary: str
    fixed_in: str | None
    imported: bool
    priority: str

    def to_dict(self) -> dict:
        return asdict(self)


def priority_for(severity: str, imported: bool) -> str:
    """Vulnerabilities in code the project really imports matter most."""
    high = severity in {"CRITICAL", "HIGH"}
    medium = severity == "MEDIUM"
    if high and imported:
        return "High"
    if high or (medium and imported):
        return "Medium"
    return "Low"


def scan(deps: list[Dependency], lookup: Callable[[str, str], list[dict]], modules: set[str]) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    errors: list[str] = []
    for dep in deps:
        try:
            vulns = lookup(dep.name, dep.version)
        except (ConnectionError, ValueError) as err:
            errors.append(f"{dep.name}=={dep.version}: {err}")
            continue
        imported = is_imported(dep.name, modules)
        for vuln in vulns:
            severity = severity_of(vuln)
            summary = (vuln.get("summary") or vuln.get("details") or "").strip().splitlines()[0:1]
            findings.append(Finding(
                package=dep.name,
                version=dep.version,
                vuln_id=vuln.get("id", "unknown"),
                severity=severity,
                summary=(summary[0] if summary else "")[:160],
                fixed_in=lowest_fix(vuln, dep.version),
                imported=imported,
                priority=priority_for(severity, imported),
            ))
    findings.sort(key=lambda f: (PRIORITY_RANK[f.priority], f.package, f.vuln_id))
    return findings, errors
