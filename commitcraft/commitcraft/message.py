"""Write a Conventional Commits message from a staged diff.

Format:  type(scope): short description
         <blank line>
         - one bullet per changed file

Types: feat, fix, docs, test, refactor, chore.
"""

from __future__ import annotations

import re
from pathlib import Path

from .diffstat import FileDiff

MAX_SUBJECT = 72
FIX_WORDS = re.compile(r"\b(fix|bug|error|null|none|crash|wrong|invalid|missing)\b", re.I)
DEF_RE = re.compile(r"^\s*(def|class|function|export)\s+\w+")
DOC_SUFFIXES = {".md", ".rst", ".txt"}
CONFIG_SUFFIXES = {".yml", ".yaml", ".toml", ".json", ".cfg", ".ini"}
VERBS = {"feat": "add", "fix": "fix", "docs": "update docs for", "test": "add tests for",
         "refactor": "refactor", "chore": "update"}


def classify(files: list[FileDiff]) -> str:
    def is_test(f: FileDiff) -> bool:
        name = Path(f.path).name
        return "tests/" in f.path or name.startswith("test_") or name.endswith("_test.py")

    if all(is_test(f) for f in files):
        return "test"
    if all(Path(f.path).suffix in DOC_SUFFIXES or f.path.startswith("docs/") for f in files):
        return "docs"
    if all(Path(f.path).suffix in CONFIG_SUFFIXES or f.path.startswith(".github/") for f in files):
        return "chore"
    added = [line for f in files for line in f.added if not is_test_line(line)]
    removed = [line for f in files for line in f.removed]
    if any(f.is_new for f in files) or any(DEF_RE.match(line) for line in added) and len(added) > len(removed):
        if not any(FIX_WORDS.search(line) for line in added):
            return "feat"
    if any(FIX_WORDS.search(line) for line in added):
        return "fix"
    if removed and abs(len(added) - len(removed)) <= max(3, len(removed) // 4):
        return "refactor"
    return "chore"


def is_test_line(line: str) -> bool:
    return bool(re.match(r"^\s*(assert\s|def test_)", line))


def scope_for(files: list[FileDiff]) -> str | None:
    if len(files) == 1:
        parts = Path(files[0].path).parts
        if len(parts) >= 2 and parts[0] != "src":
            return parts[0]
        return Path(files[0].path).stem
    tops = {Path(f.path).parts[0] for f in files if len(Path(f.path).parts) > 1}
    if len(tops) == 1:
        top = tops.pop()
        return None if top == "src" else top
    return None


def subject_for(files: list[FileDiff], kind: str) -> str:
    scope = scope_for(files)
    names = [Path(f.path).stem for f in files]
    listed = ", ".join(names[:3]) + (f" and {len(names) - 3} more" if len(names) > 3 else "")
    prefix = f"{kind}({scope})" if scope else kind
    subject = f"{prefix}: {VERBS[kind]} {listed}"
    return subject if len(subject) <= MAX_SUBJECT else subject[: MAX_SUBJECT - 3].rstrip() + "..."


def body_for(files: list[FileDiff]) -> str:
    lines = []
    for f in files:
        label = "new file" if f.is_new else "changed"
        lines.append(f"- {f.path} ({label}, +{len(f.added)} -{len(f.removed)})")
    return "\n".join(lines)


def build_message(files: list[FileDiff]) -> str:
    if not files:
        raise ValueError("nothing is staged. Use 'git add' first, then run commitcraft again.")
    kind = classify(files)
    return f"{subject_for(files, kind)}\n\n{body_for(files)}\n"


def check_message(message: str) -> list[str]:
    """Return problems with a commit message (empty list means it is fine)."""
    problems = []
    subject = message.splitlines()[0] if message else ""
    if len(subject) > MAX_SUBJECT:
        problems.append(f"subject is {len(subject)} characters; keep it under {MAX_SUBJECT}")
    if not re.match(r"^(feat|fix|docs|test|refactor|chore|perf|build|ci|style|revert)(\([^)]+\))?!?: .+", subject):
        problems.append("subject does not start with a type such as feat, fix or docs")
    return problems
