"""Summarise a diff: which files changed, and how many lines were added or removed."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FileDiff:
    path: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    is_new: bool = False


def parse_diff(text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    pending_new = False
    for line in text.splitlines():
        if line.startswith("diff --git "):
            current = None
            pending_new = False
        elif line.startswith("new file mode"):
            pending_new = True
        elif line.startswith("+++ "):
            target = line[4:].strip()
            if target == "/dev/null":
                continue
            current = FileDiff(path=target[2:] if target.startswith("b/") else target, is_new=pending_new)
            files.append(current)
        elif line.startswith("--- ") or line.startswith("@@") or current is None:
            continue
        elif line.startswith("+"):
            current.added.append(line[1:])
        elif line.startswith("-"):
            current.removed.append(line[1:])
    return files
