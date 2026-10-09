"""Parse a unified diff (the output of `git diff`) into per-file changes."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass
class FileChange:
    path: str
    added: list[tuple[int, str]] = field(default_factory=list)   # (line number in new file, text)
    removed: list[str] = field(default_factory=list)
    is_new: bool = False
    is_deleted: bool = False

    @property
    def is_test(self) -> bool:
        name = self.path.rsplit("/", 1)[-1]
        return "tests/" in self.path or "test/" in self.path or name.startswith("test_") or name.endswith("_test.py")

    @property
    def is_source(self) -> bool:
        return self.path.endswith(".py") and not self.is_test


def parse_diff(text: str) -> list[FileChange]:
    changes: list[FileChange] = []
    current: FileChange | None = None
    new_line = 0
    in_hunk = False
    pending_new = pending_deleted = False  # "new file mode" comes before the +++ line
    for line in text.splitlines():
        if line.startswith("diff --git "):
            current, in_hunk = None, False
            pending_new = pending_deleted = False
        elif not in_hunk and line.startswith("new file mode"):
            pending_new = True
        elif not in_hunk and line.startswith("deleted file mode"):
            pending_deleted = True
        elif not in_hunk and line.startswith("+++ "):
            target = line[4:].strip()
            if target == "/dev/null":
                continue
            path = target[2:] if target.startswith("b/") else target
            current = FileChange(path=path, is_new=pending_new, is_deleted=pending_deleted)
            changes.append(current)
        elif not in_hunk and line.startswith("--- "):
            continue
        elif line.startswith("@@"):
            match = HUNK_RE.match(line)
            new_line = int(match.group(1)) if match else 0
            in_hunk = True
        elif current is None or not in_hunk:
            continue
        elif line.startswith("+"):
            current.added.append((new_line, line[1:]))
            new_line += 1
        elif line.startswith("-"):
            current.removed.append(line[1:])
        elif line.startswith(" "):
            new_line += 1
    return changes
