"""Review rules. Each rule looks at the changed lines and returns findings.

These are fast, predictable checks. They catch common mistakes but do not
understand the code the way a human reviewer does.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .diffparse import FileChange

LARGE_DIFF_LINES = 400

PATTERNS = [
    # (severity, title, regex, explanation)
    ("High", "Use of eval() or exec()", re.compile(r"\b(eval|exec)\s*\("),
     "Running strings as code is a common route to code injection. Parse the input instead."),
    ("High", "Shell command with shell=True", re.compile(r"shell\s*=\s*True"),
     "shell=True passes text to the shell. Pass a list of arguments instead."),
    ("High", "Possible hard-coded secret", re.compile(r"(password|passwd|secret|api[_-]?key|token)\s*=\s*['\"][^'\"]{4,}['\"]", re.I),
     "Secrets belong in environment variables or a secret store, not in source code."),
    ("High", "SQL built from text", re.compile(r"(SELECT|INSERT|UPDATE|DELETE)\b.*(\{|%s|\+\s*[a-z_]|\+\s*['\"])", re.I),
     "Build queries with placeholders (for example ? or %s) and pass values separately."),
    ("Medium", "Bare except clause", re.compile(r"^\s*except\s*:"),
     "A bare except hides every error, including KeyboardInterrupt. Name the exception type."),
    ("Medium", "Debugging leftover", re.compile(r"\b(breakpoint\(\)|pdb\.set_trace\(|console\.log\(|debugger;)"),
     "Remove debugging calls before merging."),
    ("Low", "Unfinished work marker", re.compile(r"\b(TODO|FIXME|XXX)\b"),
     "Mark unfinished work in the issue tracker, or finish it before merging."),
]


@dataclass
class Finding:
    severity: str
    title: str
    file: str
    line: int | None
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


def line_rules(changes: list[FileChange]) -> list[Finding]:
    findings: list[Finding] = []
    for change in changes:
        for line_no, text in change.added:
            for severity, title, pattern, detail in PATTERNS:
                if pattern.search(text):
                    findings.append(Finding(severity, title, change.path, line_no, detail))
    return findings


def removed_error_handling(changes: list[FileChange]) -> list[Finding]:
    findings: list[Finding] = []
    for change in changes:
        removed = sum(1 for t in change.removed if re.match(r"^\s*except\b", t))
        added = sum(1 for _, t in change.added if re.match(r"^\s*except\b", t))
        if removed > added:
            findings.append(Finding("Medium", "Error handling removed", change.path, None,
                                    f"{removed - added} except block(s) were removed. Check that errors are still handled."))
    return findings


def missing_tests(changes: list[FileChange]) -> list[Finding]:
    sources = [c for c in changes if c.is_source and (c.added or c.removed)]
    tests = [c for c in changes if c.is_test]
    if sources and not tests:
        names = ", ".join(c.path for c in sources[:5]) + (" ..." if len(sources) > 5 else "")
        return [Finding("Medium", "No test changes", names, None,
                        f"{len(sources)} source file(s) changed but no test file did. Add or update tests.")]
    return []


def size_rule(changes: list[FileChange]) -> list[Finding]:
    total = sum(len(c.added) + len(c.removed) for c in changes)
    if total > LARGE_DIFF_LINES:
        return [Finding("Low", "Large pull request", "(whole change)", None,
                        f"{total} changed lines. Smaller pull requests are reviewed faster and more carefully.")]
    return []


def review(changes: list[FileChange]) -> list[Finding]:
    findings = line_rules(changes) + removed_error_handling(changes) + missing_tests(changes) + size_rule(changes)
    order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(findings, key=lambda f: (order[f.severity], f.file, f.line or 0))


def summarize(changes: list[FileChange]) -> dict:
    added = sum(len(c.added) for c in changes)
    removed = sum(len(c.removed) for c in changes)
    folders: dict[str, int] = {}
    for c in changes:
        top = c.path.split("/", 1)[0] if "/" in c.path else "(root)"
        folders[top] = folders.get(top, 0) + 1
    return {
        "files": len(changes),
        "added": added,
        "removed": removed,
        "new_files": sum(c.is_new for c in changes),
        "deleted_files": sum(c.is_deleted for c in changes),
        "test_files": sum(c.is_test for c in changes),
        "by_folder": dict(sorted(folders.items(), key=lambda kv: -kv[1])),
    }
