"""Compare documentation with the code and report every mismatch."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .code_index import CodeIndex

IGNORED_OPTIONS = {"--help", "--version"}
IGNORED_ENV = {"PYTHONPATH", "PATH", "HOME", "USER", "LANG", "TERM", "CI", "GITHUB_STEP_SUMMARY"}
CODE_FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SYMBOL_CALL_RE = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*\.)*([A-Za-z_][A-Za-z0-9_]*)\(\)$")
SYMBOL_CLASS_RE = re.compile(r"^[A-Z][A-Za-z0-9]+$")


@dataclass
class Issue:
    file: str
    line: int
    kind: str       # "option", "function", "class", "env var", "broken link"
    item: str
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


def _code_spans(line: str) -> list[str]:
    return INLINE_CODE_RE.findall(line)


def check_document(doc: Path, root: Path, index: CodeIndex) -> list[Issue]:
    rel = doc.relative_to(root).as_posix()
    issues: list[Issue] = []
    in_fence = False
    seen: set[tuple[str, str]] = set()

    def report(line_no: int, kind: str, item: str, message: str) -> None:
        if (kind, item) not in seen:
            seen.add((kind, item))
            issues.append(Issue(rel, line_no, kind, item, message))

    for line_no, line in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if CODE_FENCE_RE.match(line):
            in_fence = not in_fence
            continue

        if in_fence:
            for option in set(re.findall(r"(?<![\w-])(--[a-zA-Z][a-zA-Z0-9-]*)", line)):
                if option not in IGNORED_OPTIONS and option not in index.options:
                    report(line_no, "option", option, f"{option} appears in the docs but not in the code")
            for name in set(re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b", line)):
                if name not in IGNORED_ENV and name not in index.env_vars and name not in index.text:
                    report(line_no, "env var", name, f"{name} appears in the docs but not in the code")
            continue

        for span in _code_spans(line):
            call = SYMBOL_CALL_RE.match(span)
            if call and call.group(1) not in index.names:
                report(line_no, "function", call.group(1), f"`{span}` is mentioned but no such function exists")
            elif SYMBOL_CLASS_RE.match(span) and span not in index.names and span not in IGNORED_ENV:
                if len(span) > 3 and span.isalpha() and span.lower() != span and span.upper() != span:
                    report(line_no, "class", span, f"`{span}` is mentioned but no such class exists")
            for option in re.findall(r"(?<![\w-])(--[a-zA-Z][a-zA-Z0-9-]*)", span):
                if option not in IGNORED_OPTIONS and option not in index.options:
                    report(line_no, "option", option, f"{option} appears in the docs but not in the code")
            for name in re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b", span):
                if name not in IGNORED_ENV and name not in index.env_vars and name not in index.text:
                    report(line_no, "env var", name, f"{name} appears in the docs but not in the code")

        for target in LINK_RE.findall(line):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part = target.split("#", 1)[0]
            if path_part and not (doc.parent / path_part).exists():
                report(line_no, "broken link", path_part, f"link to '{path_part}' points to a file that does not exist")

    return issues


def find_docs(root: Path, doc_paths: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for entry in doc_paths:
        if entry.is_file():
            found.add(entry)
        elif entry.is_dir():
            found.update(p for p in entry.rglob("*.md") if ".git" not in p.parts)
    return sorted(found)
